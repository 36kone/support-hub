from app.core.exception_utils import ensure_403, ensure_or_400
from app.core.security import verify_password
from app.enums import TokenRole, TokenType, UserRoleEnum
from app.repositories import UserRepository
from app.schemas import SimpleUserResponse, Token
from app.services.auth.auth_token_service import AuthTokenService
from app.services.auth.mfa_service import MfaService
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic.v1 import EmailStr


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_service: AuthTokenService,
        mfa_service: MfaService,
    ) -> None:
        self._users = user_repository
        self._tokens = token_service
        self._mfa = mfa_service

    def login(
        self,
        request: Request,
        form_data: OAuth2PasswordRequestForm,
    ) -> Token | dict:
        scopes = form_data.scopes
        is_customer_scope = "customer" in scopes
        is_seller_scope = "seller" in scopes
        identifier = form_data.username.strip()

        if is_customer_scope:
            user = self._users.get_by_username(identifier, options=[])
        else:
            user = self._users.get_by_email(str(EmailStr(identifier)), options=[])

        if not user:
            raise HTTPException(400, "Invalid credentials.")

        ensure_403(
            is_seller_scope
            and user.role not in (UserRoleEnum.SELLER, UserRoleEnum.ADMIN),
            "Access denied.",
        )
        ensure_or_400(
            verify_password(form_data.password.strip(), user.password),
            "Invalid credentials.",
        )

        if user.mfa_enabled and user.mfa_secret is None:
            otp_secret, uri = self._mfa.setup(user.id)
            return {
                "access_token": self._tokens.issue_temporary_token(
                    user.id, TokenRole.MFA
                ),
                "otp_secret": otp_secret,
                "otpauth_url": uri,
            }

        if user.mfa_enabled:
            return Token(
                access_token=self._tokens.issue_temporary_token(user.id, TokenRole.MFA),
                token_type=TokenType.BEARER,
                user=SimpleUserResponse.model_validate(user),
                token_role=TokenRole.MFA,
            )

        return self._tokens.issue_user_token(
            user,
            ipv4=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
