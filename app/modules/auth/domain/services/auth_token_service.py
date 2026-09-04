from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.security import create_access_token, decode_access_token
from app.enums import TokenRole, TokenType
from app.models import User, UserSession
from app.repositories import UserSessionRepository
from app.schemas import CreateToken, SimpleUserResponse, Token
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import settings


class AuthTokenService:
    def __init__(
        self, session: Session, session_repository: UserSessionRepository
    ) -> None:
        self._session = session
        self._sessions = session_repository

    def issue_temporary_token(self, subject_id: UUID, role: TokenRole) -> str:
        return create_access_token(
            CreateToken(sub=str(subject_id), token_role=role),
            expires_delta=timedelta(minutes=5),
        )

    def get_subject(self, token: str, expected_role: TokenRole) -> UUID:
        payload = decode_access_token(token)
        if not payload or payload.get("token_role") != expected_role:
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            return UUID(payload["sub"])
        except (KeyError, TypeError, ValueError) as error:
            raise HTTPException(status_code=401, detail="Unauthorized") from error

    def issue_user_token(
        self,
        user: User,
        ipv4: str | None = None,
        user_agent: str | None = None,
    ) -> Token:
        try:
            if user.single_session:
                self._sessions.revoke_by_user_id(user.id)

            user_session = UserSession(
                id=uuid4(),
                user_id=user.id,
                expire_at=datetime.now(UTC)
                + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE),
                user_agent=user_agent,
                ipv4=ipv4,
            )
            self._sessions.add(user_session)

            access_token = create_access_token(
                CreateToken(
                    sub=str(user.id),
                    token_role=str(user.role),
                    sid=str(user_session.id),
                )
            )
            self._session.commit()

            return Token(
                access_token=access_token,
                token_type=TokenType.BEARER,
                user=SimpleUserResponse.model_validate(user),
                token_role=user.role,
            )
        except Exception:
            self._session.rollback()
            raise
