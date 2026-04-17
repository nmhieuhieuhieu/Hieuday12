import redis
from fastapi import HTTPException
from .config import settings
import time

try:
    r = redis.from_url(settings.redis_url)
    r.ping()
except Exception:
    import fakeredis
    r = fakeredis.FakeStrictRedis()

def check_rate_limit(user_id: str):
    now = time.time()
    key = f"rate_limit:{user_id}"
    
    r.zremrangebyscore(key, 0, now - 60)
    
    request_count = r.zcard(key)
    if request_count >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min")
        
    r.zadd(key, {str(now): now})
    r.expire(key, 60)
