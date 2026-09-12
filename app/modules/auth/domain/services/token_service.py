from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.presentation.schemas.auth_schema import Token
from app.modules.user.domain.services.user_session_service import UserSessionService
from app.modules.user.infraestructure.models.user_model import User
from app.modules.user.infraestructure.repositories.user_session_repository import (
    UserSessionRepository,
)
from app.modules.user.presentation.schemas.user_schema import SimpleUserResponse
from app.shared.utils.security import create_access_token, decode_access_token


class TokenService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.sessions = UserSessionRepository(session)

    def issue_temporary_token(self, subject_id: UUID, role: str) -> str:
        return create_access_token(
            str(subject_id), expires_delta=timedelta(minutes=5), token_role=role
        )

    def get_subject(self, token: str, expected_role: str) -> UUID:
        payload = decode_access_token(token)
        if payload is None or payload.get("token_role") != expected_role:
            raise HTTPException(status_code=401, detail="Unauthorized")
        try:
            return UUID(str(payload["sub"]))
        except (KeyError, TypeError, ValueError) as error:
            raise HTTPException(status_code=401, detail="Unauthorized") from error

    async def issue_user_token(
        self, user: User, ipv4: str | None = None, user_agent: str | None = None
    ) -> Token:
        user_session = await UserSessionService(self.session).create_user_session(
            user, ipv4, user_agent
        )
        return Token(
            access_token=create_access_token(str(user.id), str(user_session.id)),
            user=SimpleUserResponse.model_validate(user),
        )
