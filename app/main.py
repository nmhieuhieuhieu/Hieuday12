import os
import time
import signal
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    # Fallback if utils.llm is missing
    def llm_ask(question): return f"Fallback mock response for: {question}"

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger(__name__)

_is_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info("Application startup")
    _is_ready = True
    yield
    _is_ready = False
    logger.info("Application shutdown")

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Phục vụ thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    """Giao diện chính"""
    return FileResponse("static/index.html")

class AskRequest(BaseModel):
    question: str = Field(..., description="Your question for the agent")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    if not _is_ready:
        return Response(status_code=503, content='{"status": "not ready"}')
    try:
        redis_client.ping()
        return {"status": "ready"}
    except Exception:
        return Response(status_code=503, content='{"status": "redis not ready"}')

@app.post("/ask")
def ask(
    body: AskRequest,
    user_id: str = Depends(verify_api_key)
):
    check_rate_limit(user_id)
    check_budget(user_id, 0.001)  # Simulate 0.001$ cost per request
    
    # Stateless design: store and retrieve history from Redis
    history_key = f"history:{user_id}"
    history = redis_client.lrange(history_key, 0, -1)
    
    answer = llm_ask(body.question)
    
    # Save to Redis
    redis_client.rpush(history_key, f"Q: {body.question}")
    redis_client.rpush(history_key, f"A: {answer}")
    redis_client.expire(history_key, 3600)  # Expire history after 1 hour
    
    return {
        "question": body.question,
        "answer": answer,
        "model": settings.llm_model,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def shutdown_handler(signum, frame):
    logger.info("Graceful shutdown triggered")
    import sys
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
