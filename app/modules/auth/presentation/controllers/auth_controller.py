from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infraestructure.database.database import get_db
from app.modules.auth.presentation.schemas.auth_schema import LoginRequest, TokenResponse
from app.modules.user.infraestructure.models.user_session_model import UserSession
from app.modules.user.infraestructure.repositories.user_repository import UserRepository
from app.modules.user.infraestructure.repositories.user_session_repository import (
    UserSessionRepository,
)
from app.shared.utils.security import create_access_token, verify_password

auth_router = APIRouter()


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, request: Request, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    users = UserRepository(session)
    user = await users.get_by_email(data.email)
    if user is None or not user.is_active or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    sessions = UserSessionRepository(session)
    if user.single_session:
        await sessions.revoke_all_for_user(user.id)
    user_session = UserSession(
        id=uuid4(),
        user_id=user.id,
        expire_at=datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE),
        user_agent=request.headers.get("user-agent"),
        ipv4=request.client.host if request.client else None,
    )
    await sessions.create(user_session)
    await session.commit()
    return TokenResponse(
        access_token=create_access_token(str(user.id), str(user_session.id))
    )
