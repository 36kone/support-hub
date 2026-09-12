from uuid import UUID

import pyotp
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.services.token_service import TokenService
from app.modules.auth.presentation.schemas.auth_schema import Enable2FARequest, Token
from app.modules.user.infraestructure.repositories.user_repository import UserRepository


class MfaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.tokens = TokenService(session)

    async def _get_user(self, user_id: UUID):
        user = await self.users.get(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def verify(
        self, code: str, token: str, ipv4: str | None, user_agent: str | None
    ) -> Token:
        user = await self._get_user(self.tokens.get_subject(token, "mfa"))
        if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(code):
            raise HTTPException(status_code=400, detail="Invalid code")
        return await self.tokens.issue_user_token(user, ipv4, user_agent)

    async def setup(self, user_id: UUID) -> tuple[str, str]:
        user = await self._get_user(user_id)
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        await self.session.commit()
        return secret, pyotp.TOTP(secret).provisioning_uri(
            name=user.email, issuer_name="Support Hub"
        )

    async def enable(self, payload: Enable2FARequest, user_id: UUID) -> dict[str, str]:
        user = await self._get_user(user_id)
        if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(payload.code):
            raise HTTPException(status_code=400, detail="Invalid code")
        user.mfa_enabled = True
        await self.session.commit()
        return {"message": "2FA activated"}

    async def disable(self, user_id: UUID) -> dict[str, str]:
        user = await self._get_user(user_id)
        if not user.mfa_enabled:
            raise HTTPException(status_code=400, detail="2FA already disabled")
        user.mfa_enabled = False
        user.mfa_secret = None
        await self.session.commit()
        return {"message": "2FA disabled"}
