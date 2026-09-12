from pydantic import EmailStr

from app.modules.user.presentation.schemas.user_schema import SimpleUserResponse
from app.shared.utils.base_schema import BaseSchema


class LoginRequest(BaseSchema):
    email: str
    password: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"


class Token(TokenResponse):
    user: SimpleUserResponse | None = None
    token_role: str | None = None


class VerifyUserByPassword(BaseSchema):
    password: str


class ChangePasswordRequest(BaseSchema):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseSchema):
    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    token: str
    new_password: str


class Enable2FARequest(BaseSchema):
    code: str


class Message(BaseSchema):
    message: str
