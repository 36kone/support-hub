from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infraestructure.database.database import get_db
from app.modules.user.infraestructure.models.user_model import User
from app.modules.user.infraestructure.repositories.user_repository import UserRepository
from app.modules.user.infraestructure.repositories.user_session_repository import (
    UserSessionRepository,
)
from app.shared.utils.security import decode_access_token

bearer_scheme = HTTPBearer()


async def get_auth_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    try:
        user_id, session_id = UUID(payload["sub"]), UUID(payload["sid"])
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from error
    user = await UserRepository(session).get(user_id)
    active_session = await UserSessionRepository(session).get_active(session_id, user_id)
    if user is None or not user.is_active or active_session is None:
        raise HTTPException(status_code=401, detail="Session is no longer valid")
    return user
