import os
import time
import signal
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit, r as redis_client
from app.cost_guard import check_budget

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.llm import ask as llm_ask
except ImportError:
    def llm_ask(question): return f"Fallback mock response for: {question}"

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}'
)
logger = logging.getLogger(__name__)

_is_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info("Application startup — binding on port %s", os.getenv("PORT", "8000"))
    _is_ready = True
    yield
    _is_ready = False
    logger.info("Application shutdown")

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if not os.path.isdir(STATIC_DIR):
    # fallback: look relative to CWD
    STATIC_DIR = os.path.join(os.getcwd(), "static")

logger.info("Static dir resolved to: %s (exists=%s)", STATIC_DIR, os.path.isdir(STATIC_DIR))

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    logger.warning("Static directory not found — UI will not be served")

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse({"message": "AI Agent API is running", "version": settings.app_version})

class AskRequest(BaseModel):
    question: str = Field(..., description="Your question for the agent")

@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}

@app.get("/ready")
def ready():
    if not _is_ready:
        return Response(status_code=503, content='{"status":"not ready"}')
    try:
        redis_client.ping()
        return {"status": "ready"}
    except Exception:
        return Response(status_code=503, content='{"status":"redis not ready"}')

@app.post("/ask")
def ask(
    body: AskRequest,
    user_id: str = Depends(verify_api_key)
):
    check_rate_limit(user_id)
    check_budget(user_id, 0.001)

    history_key = f"history:{user_id}"
    history = redis_client.lrange(history_key, 0, -1)

    answer = llm_ask(body.question)

    redis_client.rpush(history_key, f"Q: {body.question}")
    redis_client.rpush(history_key, f"A: {answer}")
    redis_client.expire(history_key, 3600)

    return {
        "question": body.question,
        "answer": answer,
        "model": settings.llm_model,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def shutdown_handler(signum, frame):
    logger.info("Graceful shutdown triggered")
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
