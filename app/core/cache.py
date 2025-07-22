import json
from typing import Any, Optional
from functools import wraps

# Type annotations for Redis
try:
    import aioredis
    from aioredis import Redis, ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None
    ConnectionPool = None

from .config import settings

class CacheService:
    """Redis-based cache service for high performance."""
    
    def __init__(self):
        self.redis: Optional[Any] = None
        self._connection_pool: Optional[Any] = None
    
    async def connect(self):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE or not settings.cache_enabled:
            return
            
        if not self.redis and ConnectionPool and Redis:
            self._connection_pool = ConnectionPool.from_url(
                settings.redis_url,
                password=settings.redis_password,
                db=settings.redis_db,
                max_connections=settings.redis_max_connections,
                decode_responses=True
            )
            self.redis = Redis(connection_pool=self._connection_pool)
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not settings.cache_enabled or not REDIS_AVAILABLE:
            return None
        
        try:
            await self.connect()
            if self.redis:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not settings.cache_enabled or not REDIS_AVAILABLE:
            return False
        
        try:
            await self.connect()
            if self.redis:
                ttl = ttl or settings.cache_ttl
                serialized_value = json.dumps(value, default=str)
                return await self.redis.setex(key, ttl, serialized_value)
            return False
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not settings.cache_enabled or not REDIS_AVAILABLE:
            return False
        
        try:
            await self.connect()
            if self.redis:
                return bool(await self.redis.delete(key))
            return False
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not settings.cache_enabled or not REDIS_AVAILABLE:
            return False
        
        try:
            await self.connect()
            if self.redis:
                return bool(await self.redis.exists(key))
            return False
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not settings.cache_enabled or not REDIS_AVAILABLE:
            return 0
        
        try:
            await self.connect()
            if self.redis:
                keys = await self.redis.keys(pattern)
                if keys:
                    return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not settings.cache_enabled:
            return {"enabled": False}
        
        if not REDIS_AVAILABLE:
            return {"enabled": False, "error": "Redis not available"}
        
        try:
            await self.connect()
            if self.redis:
                info = await self.redis.info()
                return {
                    "enabled": True,
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
            return {"enabled": True, "error": "Redis not connected"}
        except Exception as e:
            return {"enabled": True, "error": str(e)}

# Global cache instance
cache_service = CacheService()

def cache_result(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Decorator to invalidate cache after function execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await cache_service.clear_pattern(pattern)
            return result
        return wrapper
    return decorator 