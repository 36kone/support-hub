import redis.asyncio as redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend


def init_cache(redis_url: str | None = None) -> redis.Redis | None:
    if redis_url is None:
        FastAPICache.init(InMemoryBackend(), prefix="support-hub-cache")
        return None

    cache_redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=False)
    FastAPICache.init(RedisBackend(cache_redis), prefix="support-hub-cache")

    return cache_redis
