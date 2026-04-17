import redis
from fastapi import HTTPException
from .config import settings
from datetime import datetime

try:
    r = redis.from_url(settings.redis_url)
    r.ping()
except Exception:
    import fakeredis
    r = fakeredis.FakeStrictRedis()

def check_budget(user_id: str, estimated_cost: float = 0.0) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current = float(r.get(key) or 0)
    
    if current + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(status_code=503, detail="Monthly budget exhausted.")
        
    if estimated_cost > 0:
        r.incrbyfloat(key, estimated_cost)
        r.expire(key, 32 * 24 * 3600)  # 32 days
        
    return True
