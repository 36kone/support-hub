from uuid import UUID

import pyotp
from app.core.exception_utils import ensure_or_400, ensure_or_404
from app.enums import TokenRole
from app.repositories import UserRepository
from app.schemas import Enable2FARequest, Token
from app.services.auth.auth_token_service import AuthTokenService
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


class MfaService:
    def __init__(
        self,
        session: Session,
        user_repository: UserRepository,
        token_service: AuthTokenService,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._tokens = token_service

    def _get_user(self, user_id: UUID):
        return ensure_or_404(
            self._users.get(user_id, options=[]),
            "User not found",
        )

    def verify(self, code: str, request: Request, token: str) -> Token:
        user_id = self._tokens.get_subject(token, TokenRole.MFA)
        user = self._get_user(user_id)

        if not user.mfa_secret:
            raise HTTPException(400, "Missing MFA setup")

        ensure_or_400(pyotp.TOTP(user.mfa_secret).verify(code), "Invalid code")

        return self._tokens.issue_user_token(
            user,
            ipv4=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    def setup(self, user_id: UUID) -> tuple[str, str]:
        user = self._get_user(user_id)
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        self._users.add(user)
        self._session.commit()

        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="Impacto",
        )
        return secret, uri

    def enable(self, payload: Enable2FARequest, user_id: UUID) -> dict:
        user = self._get_user(user_id)
        if not user.mfa_secret:
            raise HTTPException(400, "Missing MFA setup")

        ensure_or_400(pyotp.TOTP(user.mfa_secret).verify(payload.code), "Invalid code")
        user.mfa_enabled = True
        self._users.add(user)
        self._session.commit()
        return {"message": "2FA activated"}

    def disable(self, user_id: UUID) -> dict:
        user = self._get_user(user_id)
        ensure_or_400(user.mfa_enabled, "2FA already disabled")

        user.mfa_enabled = False
        user.mfa_secret = None
        self._users.add(user)
        self._session.commit()
        return {"message": "2fa disabled"}
