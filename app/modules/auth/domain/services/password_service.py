import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infraestructure.email.email_sender import EmailSender
from app.modules.auth.presentation.schemas.auth_schema import (
    ChangePasswordRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.modules.user.domain.services.user_service import UserService
from app.modules.user.domain.services.user_session_service import UserSessionService
from app.shared.utils.security import get_password_hash, verify_password


class PasswordService:
    def __init__(self, session: AsyncSession, email_sender: EmailSender | None = None) -> None:
        self.session = session
        self.users = UserService(session)
        self.sessions = UserSessionService(session)
        self.email_sender = email_sender or EmailSender()

    async def change(self, data: ChangePasswordRequest, user_id: UUID) -> dict[str, str]:
        user = await self.users.get_by_id(user_id)
        if not verify_password(data.current_password, user.password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.password = get_password_hash(data.new_password)
        await self.session.commit()
        await self.sessions.invalidate_user_cache(user.id)
        return {"message": "Password changed successfully"}

    async def request_reset(self, data: PasswordResetRequest) -> dict[str, str]:
        user = await self.users.get_by_email(str(data.email))
        if user is None:
            raise HTTPException(status_code=404, detail="Invalid credentials")
        user.password_recovery = secrets.token_urlsafe(32)
        user.password_recovery_expire = datetime.now(UTC) + timedelta(hours=1)
        await self.session.commit()
        await self.email_sender.send_email(
            subject="Password reset",
            email_to=data.email,
            template_path="app/templates/password_reset.html",
            context={
                "username": user.name,
                "reset_url": f"{settings.ADMIN_BASE_URL}/reset-password?token={user.password_recovery}",
            },
        )
        return {"message": "Password reset email sent"}

    async def confirm_reset(self, data: PasswordResetConfirm) -> dict[str, str]:
        user = await self.users.get_by_password_reset_token(data.token)
        user.password = get_password_hash(data.new_password)
        user.password_recovery = None
        user.password_recovery_expire = None
        await self.session.commit()
        await self.sessions.revoke_user_sessions(user.id)
        return {"message": "Password reset successfully"}
