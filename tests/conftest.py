"""Test infrastructure backed by isolated PostgreSQL and Redis containers."""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


def pytest_configure(config: pytest.Config) -> None:
    """Start test dependencies before application settings are imported."""
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer

    postgres = PostgresContainer("postgres:18-alpine", driver="asyncpg")
    redis = RedisContainer("redis:8-alpine")
    postgres.start()
    redis.start()

    os.environ["DATABASE_URL"] = postgres.get_connection_url()
    os.environ["REDIS_URL"] = (
        f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}/0"
    )
    os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE"] = "60"
    config._postgres_container = postgres  # type: ignore[attr-defined]
    config._redis_container = redis  # type: ignore[attr-defined]


def pytest_unconfigure(config: pytest.Config) -> None:
    for name in ("_redis_container", "_postgres_container"):
        container = getattr(config, name, None)
        if container is not None:
            container.stop()


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Imports happen after pytest_configure has supplied the container URLs.
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
