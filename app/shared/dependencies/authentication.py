import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.security import decode_access_token
from app.db.database import get_db
from app.enums import UserRoleEnum
from app.enums.token import TokenRole
from app.models import User, UserSession
from app.models.user.user_profile_model import UserProfile
from app.redis.redis import redis_client
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
bearer_scheme = HTTPBearer(auto_error=False)


def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e


def get_mfa_user(
    bearer: HTTPAuthorizationCredentials = Security(bearer_scheme),
    oauth2: str | None = Depends(oauth2_scheme),
) -> User:
    token = bearer.credentials if bearer else oauth2
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("token_role") != TokenRole.MFA:
        raise credentials_exception

    try:
        user_id = UUID(payload.get("sub"))
    except Exception as e:
        raise credentials_exception from e

    with get_db() as db:
        user = db.scalar(
            select(User).options(joinedload(User.profile)).where(User.id == user_id)
        )

    if not user:
        raise credentials_exception

    return user


def _fetch_user_from_db(
    user_id: UUID, session_id: UUID
) -> tuple[User, UserSession] | None:
    query = (
        select(User, UserSession)
        .options(joinedload(User.profile))
        .join(UserSession, UserSession.user_id == User.id)
        .where(User.id == user_id, UserSession.id == session_id)
    )

    with get_db() as db:
        result = db.execute(query).first()
        if result:
            user, user_session = result
            _ = user.profile
            return user, user_session
        return None


async def get_auth_user(
    bearer: HTTPAuthorizationCredentials = Security(bearer_scheme),
    oauth2: str | None = Depends(oauth2_scheme),
) -> User:
    token = bearer.credentials if bearer else oauth2
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("token_role") == TokenRole.MFA:
        raise credentials_exception

    try:
        user_id = UUID(payload.get("sub"))
        session_id = UUID(payload.get("sid"))
    except Exception as e:
        raise credentials_exception from e

    # 1. Tenta buscar a sessão diretamente no Redis
    cache_key = f"auth:session:{session_id}:user:{user_id}"
    redis = await redis_client.get_client()

    cached_user = await redis.get(cache_key)

    if cached_user:
        # Cache Hit: Remonta os objetos do SQLAlchemy usando o JSON armazenado
        user_data = json.loads(cached_user)
        profile_data = user_data.pop("profile", None)

        user_data["id"] = UUID(user_data["id"])

        if user_data.get("customer_id"):
            user_data["customer_id"] = UUID(user_data["customer_id"])

        user = User(**user_data)

        if profile_data:
            profile_data["id"] = UUID(profile_data["id"])
            user.profile = UserProfile(**profile_data)

        return user

    # 2. Cache Miss: Busca no DB de forma não-bloqueante
    result = await run_in_threadpool(_fetch_user_from_db, user_id, session_id)

    if not result:
        raise credentials_exception

    user, user_session = result

    now_utc = datetime.now(UTC)

    expire_at = user_session.expire_at
    if expire_at.tzinfo is None:
        expire_at = expire_at.replace(tzinfo=UTC)

    revoked_at = user_session.revoked_at
    if revoked_at is not None and revoked_at.tzinfo is None:
        revoked_at = revoked_at.replace(tzinfo=UTC)

    if revoked_at is not None or expire_at < now_utc:
        raise credentials_exception

    # 3. Salva no Redis (Sessão Válida)
    user_dict = {
        "id": str(user.id),
        "customer_id": str(user.customer_id) if user.customer_id else None,
        "name": user.name,
        "username": user.username,
        "phone": user.phone,
        "email": user.email,
        "document": user.document,
        "role": user.role,
        "role_type": user.role_type,
        "super_user": user.super_user,
        "allow_virtual_agent": user.allow_virtual_agent,
        "lat": user.lat,
        "lng": user.lng,
    }

    if user.profile:
        user_dict["profile"] = {"id": str(user.profile.id)}

    ttl_seconds = int((expire_at - now_utc).total_seconds())

    if ttl_seconds > 0:
        await redis.setex(name=cache_key, time=ttl_seconds, value=json.dumps(user_dict))

    return user


def auth_guard(
    request: Request,
    user: User = Depends(get_auth_user),
) -> None:
    endpoint = request.scope.get("endpoint")

    if endpoint is None:
        return

    roles = getattr(endpoint, "__required_roles__", [])
    profiles = getattr(endpoint, "__required_profiles__", [])

    if user.role == UserRoleEnum.ADMIN or user.super_user:
        return

    if roles and user.role not in roles:
        raise HTTPException(status_code=403, detail="Forbidden")

    if profiles:
        profile_id = getattr(getattr(user, "profile", None), "id", None)
        if profile_id not in profiles:
            raise HTTPException(status_code=403, detail="Forbidden")


def required_permissions(
    *, roles: list[str] | None = None, profiles: list[str] | None = None
) -> Callable:
    def decorator(func: Any):
        func.__required_roles__ = roles or []
        func.__required_profiles__ = profiles or []
        return func

    return decorator
