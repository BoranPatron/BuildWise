import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict
from .config import get_settings

settings = get_settings()

class RateLimiter:
    """In-memory rate limiter for API protection."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        """Check if request is allowed based on rate limit."""
        async with self.lock:
            now = time.time()
            window_start = now - window_seconds
            
            # Clean old requests
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
            
            # Check if limit exceeded
            if len(self.requests[key]) >= max_requests:
                return False, {
                    "limit_exceeded": True,
                    "remaining": 0,
                    "reset_time": window_start + window_seconds,
                    "current_requests": len(self.requests[key])
                }
            
            # Add current request
            self.requests[key].append(now)
            
            return True, {
                "limit_exceeded": False,
                "remaining": max_requests - len(self.requests[key]),
                "reset_time": window_start + window_seconds,
                "current_requests": len(self.requests[key])
            }
    
    async def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> Dict:
        """Get remaining requests for a key."""
        async with self.lock:
            now = time.time()
            window_start = now - window_seconds
            
            # Clean old requests
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
            
            return {
                "remaining": max(0, max_requests - len(self.requests[key])),
                "reset_time": window_start + window_seconds,
                "current_requests": len(self.requests[key])
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get client IP
        client_ip = scope.get("client", ("unknown", 0))[0]
        
        # Check rate limit
        allowed, limit_info = await rate_limiter.is_allowed(
            client_ip,
            settings.rate_limit_requests_per_minute,
            60
        )
        
        if not allowed:
            # Return rate limit exceeded response
            response = {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"x-ratelimit-remaining", str(limit_info["remaining"]).encode()),
                    (b"x-ratelimit-reset", str(int(limit_info["reset_time"])).encode()),
                ]
            }
            await send(response)
            
            body = {
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": int(limit_info["reset_time"] - time.time())
            }
            
            await send({
                "type": "http.response.body",
                "body": str(body).encode()
            })
            return
        
        # Add rate limit headers to response
        original_send = send
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                message["headers"].extend([
                    (b"x-ratelimit-remaining", str(limit_info["remaining"]).encode()),
                    (b"x-ratelimit-reset", str(int(limit_info["reset_time"])).encode()),
                ])
            await original_send(message)
        
        await self.app(scope, receive, send_with_headers)

def rate_limit(max_requests: int, window_seconds: int = 60):
    """Decorator for rate limiting specific endpoints."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get client identifier (IP or user ID)
            client_id = "default"  # This should be extracted from request context
            
            allowed, limit_info = await rate_limiter.is_allowed(
                f"{func.__name__}:{client_id}",
                max_requests,
                window_seconds
            )
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": int(limit_info["reset_time"] - time.time())
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator 