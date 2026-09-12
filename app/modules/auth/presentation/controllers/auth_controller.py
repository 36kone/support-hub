import logging

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.modules.auth.domain.services.auth_service import AuthService
from app.modules.auth.domain.services.mfa_service import MfaService
from app.modules.auth.domain.services.password_service import PasswordService
from app.modules.auth.infraestructure.factories.auth_factory import build_auth_service
from app.modules.auth.infraestructure.factories.mfa_factory import build_mfa_service
from app.modules.auth.infraestructure.factories.password_factory import (
    build_password_service,
)
from app.modules.auth.presentation.schemas.auth_schema import (
    ChangePasswordRequest,
    Enable2FARequest,
    Message,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    VerifyUserByPassword,
)
from app.modules.user.domain.services.user_service import UserService
from app.modules.user.infraestructure.factories.user_factory import build_user_service
from app.modules.user.infraestructure.models.user_model import User
from app.modules.user.presentation.schemas.user_schema import (
    SimpleUserResponse,
    UpdateCurrentUser,
    UserResponse,
)
from app.shared.dependencies.authentication import get_mfa_user, oauth2_scheme
from app.shared.dependencies.current_user import CurrentUser
from app.shared.dependencies.service_provider import get_service
from app.shared.utils.cbv import cbv

auth_router = APIRouter()
logger = logging.getLogger("auth")


@cbv(auth_router)
class AuthController:
    service: AuthService = Depends(get_service(build_auth_service))
    user_service: UserService = Depends(get_service(build_user_service))
    password_service: PasswordService = Depends(get_service(build_password_service))
    mfa_service: MfaService = Depends(get_service(build_mfa_service))

    @auth_router.post("/login", response_model=Token)
    async def login(
        self,
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
    ) -> Token:
        return await self.service.login(
            form_data.username,
            form_data.password,
            request.client.host if request.client else None,
            request.headers.get("user-agent"),
        )

    @auth_router.post("/verify-by-password")
    async def verify_user_by_password(
        self, current_user: CurrentUser, data: VerifyUserByPassword
    ) -> bool:
        return await self.user_service.verify_by_password(data.password, current_user.id)

    @auth_router.get("/me", response_model=SimpleUserResponse)
    async def read_current_user(self, current_user: CurrentUser) -> SimpleUserResponse:
        return SimpleUserResponse.model_validate(current_user)

    @auth_router.put("/me", response_model=UserResponse)
    async def update_authenticated_user(
        self, data: UpdateCurrentUser, current_user: CurrentUser
    ) -> UserResponse:
        user = await self.user_service.update_current_user(data, current_user.id)
        return UserResponse.model_validate(user)

    @auth_router.post("/forgot-password", response_model=Message)
    async def request_password_reset(self, data: PasswordResetRequest) -> Message:
        return Message(**(await self.password_service.request_reset(data)))

    @auth_router.put("/change-password", response_model=Message)
    async def change_password(
        self, data: ChangePasswordRequest, current_user: CurrentUser
    ) -> Message:
        return Message(**(await self.password_service.change(data, current_user.id)))

    @auth_router.post("/reset-password", response_model=Message)
    async def confirm_password_reset(self, data: PasswordResetConfirm) -> Message:
        return Message(**(await self.password_service.confirm_reset(data)))

    @auth_router.post("/verify-2fa/{code}", response_model=Token)
    async def verify_2fa(
        self, code: str, request: Request, token: str = Depends(oauth2_scheme)
    ) -> Token:
        return await self.mfa_service.verify(
            code,
            token,
            request.client.host if request.client else None,
            request.headers.get("user-agent"),
        )

    @auth_router.post("/setup-2fa")
    async def setup_2fa(self, current_user: User = Depends(get_mfa_user)) -> dict[str, str]:
        secret, uri = await self.mfa_service.setup(current_user.id)
        return {"otp_secret": secret, "otpauth_url": uri}

    @auth_router.post("/me/setup-2fa")
    async def setup_2fa_for_authenticated_user(self, current_user: CurrentUser) -> dict[str, str]:
        secret, uri = await self.mfa_service.setup(current_user.id)
        return {"otp_secret": secret, "otpauth_url": uri}

    @auth_router.post("/enable-2fa", response_model=Message)
    async def enable_2fa(self, payload: Enable2FARequest, current_user: CurrentUser) -> Message:
        return Message(**(await self.mfa_service.enable(payload, current_user.id)))

    @auth_router.post("/disable-2fa", response_model=Message)
    async def disable_2fa(self, current_user: CurrentUser) -> Message:
        return Message(**(await self.mfa_service.disable(current_user.id)))
