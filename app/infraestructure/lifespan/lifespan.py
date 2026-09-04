from contextlib import asynccontextmanager

from app.core.cache import init_cache
from app.rabbitmq.consumer import RabbitConsumer
from app.redis.redis import redis_client
from app.websockets.manager import ws_manager
from fastapi import FastAPI

from app.core import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.connect()
    cache_redis = init_cache(settings.REDIS_URL)
    await ws_manager.init_redis()

    consumer = RabbitConsumer()
    app.state.rabbitmq_consumer = consumer

    await consumer.start()

    try:
        yield
    finally:
        await consumer.stop()
        await ws_manager.close_redis()
        if cache_redis is not None:
            await cache_redis.aclose()
        await redis_client.disconnect()
