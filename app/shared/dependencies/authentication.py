from datetime import UTC, datetime
from uuid import UUID

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jwt import InvalidTokenError, decode
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infraestructure.database.database import get_db
from app.modules.user.infraestructure.models.user_model import User
from app.modules.user.infraestructure.repositories.user_repository import UserRepository
from app.modules.user.infraestructure.repositories.user_session_repository import (
    UserSessionRepository,
)
from app.shared.utils.security import decode_access_token

MFA_TOKEN_ROLE = "mfa"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise _credentials_exception()
    try:
        return decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except InvalidTokenError as error:
        raise _credentials_exception() from error


async def get_mfa_user(
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    oauth2: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    token = bearer.credentials if bearer else oauth2
    payload = decode_access_token(token) if token else None
    if payload is None or payload.get("token_role") != MFA_TOKEN_ROLE:
        raise _credentials_exception()
    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as error:
        raise _credentials_exception() from error
    user = await UserRepository(session).get(user_id)
    if user is None:
        raise _credentials_exception()
    return user


async def get_auth_user(
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    oauth2: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    token = bearer.credentials if bearer else oauth2
    payload = decode_access_token(token) if token else None
    if payload is None or payload.get("token_role") == MFA_TOKEN_ROLE:
        raise _credentials_exception()
    try:
        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"])
    except (KeyError, ValueError) as error:
        raise _credentials_exception() from error

    cache = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        cache_key = f"auth:session:{session_id}:user:{user_id}"
        if not await cache.exists(cache_key):
            active_session = await UserSessionRepository(session).get_active(session_id, user_id)
            if active_session is None:
                raise _credentials_exception()
            ttl_seconds = int((active_session.expire_at - datetime.now(UTC)).total_seconds())
            if ttl_seconds > 0:
                await cache.set(cache_key, "valid", ex=ttl_seconds)
    finally:
        await cache.aclose()

    user = await UserRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise _credentials_exception()
    return user
