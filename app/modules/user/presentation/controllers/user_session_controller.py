from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infraestructure.database.database import get_db
from app.modules.user.infraestructure.repositories.user_session_repository import (
    UserSessionRepository,
)
from app.modules.user.presentation.schemas.user_session_schema import UserSessionResponse
from app.shared.dependencies.authentication import bearer_scheme
from app.shared.dependencies.current_user import CurrentUser
from app.shared.utils.security import decode_access_token

user_session_router = APIRouter()


@user_session_router.get("", response_model=list[UserSessionResponse])
async def list_sessions(current_user: CurrentUser, session: AsyncSession = Depends(get_db)):
    return await UserSessionRepository(session).list_by_user(current_user.id)


@user_session_router.delete("/current", status_code=204)
async def revoke_current_session(
    current_user: CurrentUser,
    credentials=Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> None:
    payload = decode_access_token(credentials.credentials)
    session_id = UUID(payload["sid"]) if payload else None
    if session_id is None or not await UserSessionRepository(session).revoke(session_id, current_user.id):
        raise HTTPException(status_code=401, detail="Session is no longer valid")
    await session.commit()
