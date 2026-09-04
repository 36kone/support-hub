import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.exception_utils import ensure_or_400, ensure_or_404
from app.core.security import get_password_hash, verify_password
from app.dependencies.email import EmailSender
from app.repositories import UserRepository
from app.schemas import (
    ChangePasswordRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.services.user.user_session_service import UserSessionService
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings


class PasswordService:
    def __init__(
        self,
        session: Session,
        user_repository: UserRepository,
        email_sender: EmailSender,
        user_session_service: UserSessionService,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._email_sender = email_sender
        self._user_session_service = user_session_service

    async def change(self, data: ChangePasswordRequest, user_id: UUID) -> dict:
        user = ensure_or_404(
            self._users.get(user_id, options=[]),
            "User not found",
        )
        ensure_or_400(
            verify_password(data.current_password, user.password),
            "Current password is incorrect",
        )

        user.password = get_password_hash(data.new_password)
        self._users.add(user)
        self._session.commit()

        await self._user_session_service.invalidate_user_cache(user.id)

        return {"message": "Password changed successfully"}

    async def request_reset(self, data: PasswordResetRequest) -> dict:
        user = self._users.get_by_email(str(data.email), options=[])
        if not user:
            raise HTTPException(404, "Invalid credentials.")

        reset_token = secrets.token_urlsafe(32)
        user.password_recovery = reset_token
        user.password_recovery_expire = datetime.now(UTC) + timedelta(hours=1)
        self._users.add(user)
        self._session.commit()

        reset_url = f"{settings.ADMIN_BASE_URL}/reset-password?token={reset_token}"

        await self._email_sender.send_email(
            subject="Recuperação de Senha",
            email_to=data.email,
            template_path="app/templates/password_reset.html",
            context={"username": user.name, "reset_url": reset_url},
        )
        return {"message": "Email for reset password sent successfully"}

    async def confirm_reset(self, data: PasswordResetConfirm) -> dict:
        user = ensure_or_400(
            self._users.get_by_password_reset_token(data.token, options=[]),
            "Token inválido ou expirado",
        )

        try:
            user.password = get_password_hash(data.new_password)
            user.password_recovery = None
            user.password_recovery_expire = None
            self._users.add(user)
            self._session.commit()
        except Exception as error:
            self._session.rollback()
            raise HTTPException(
                status_code=400, detail="Password update failed"
            ) from error

        await self._user_session_service.invalidate_user_cache(user.id)

        return {"message": "Senha redefinida com sucesso"}
