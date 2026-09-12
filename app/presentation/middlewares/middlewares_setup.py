import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.dependencies.limiter import limiter, rate_limit_exceeded_handler
from app.middlewares.timing_middleware import add_timing_middleware

timing_logger = logging.getLogger("timing")


def configure_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.limiter = limiter  # type: ignore
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    add_timing_middleware(app, record=timing_logger.info, exclude="health")
