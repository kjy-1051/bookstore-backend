# app/middleware/rate_limit.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis import r


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        key = f"rate:{ip}"

        # 요청 카운트 증가
        count = r.incr(key)

        # 첫 요청이면 TTL 설정
        if count == 1:
            r.expire(key, 60)  # 60초 윈도우

        if count > 60:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )

        return await call_next(request)
