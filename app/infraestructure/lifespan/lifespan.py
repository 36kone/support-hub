from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.infraestructure.cache.cache import init_cache
from app.infraestructure.database.database import create_database_schema, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_database_schema()
    cache_redis = init_cache(settings.REDIS_URL)

    try:
        yield
    finally:
        if cache_redis is not None:
            await cache_redis.aclose()
        await engine.dispose()
