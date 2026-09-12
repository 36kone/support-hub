from datetime import datetime
from uuid import UUID

from pydantic import EmailStr

from app.shared.utils.base_schema import BaseSchema


class CreateUser(BaseSchema):
    name: str
    email: EmailStr
    password: str
    phone: str = ""
    single_session: bool | None = True
    mfa_enabled: bool | None = False
    is_super_user: bool = False


class UserSearchRequest(BaseSchema):
    keyword: str | None = None
    size: int = 10
    page: int = 1


class UserResponse(BaseSchema):
    id: UUID
    name: str
    email: str
    phone: str
    is_active: bool
    is_super_user: bool
    mfa_enabled: bool | None = None
    single_session: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UpdateCurrentUser(BaseSchema):
    name: str
    email: str
    phone: str


class UpdateUser(BaseSchema):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    is_super_user: bool | None = None
    mfa_enabled: bool | None = None
    single_session: bool | None = None


class SimpleUserResponse(BaseSchema):
    id: UUID
    name: str
    phone: str
    email: EmailStr
    is_super_user: bool
    is_admin: bool
