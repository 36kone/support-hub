from datetime import datetime
from uuid import UUID

from app.shared.utils.base_schema import BaseSchema


class CreateUserSession(BaseSchema):
    user_id: UUID | None = None
    expire_at: datetime | None = None
    user_agent: str | None = None
    user_device: str | None = None
    revoked_at: datetime | None = None
    ipv4: str | None = None
    ipv6: str | None = None


class UserSessionSearchRequest(BaseSchema):
    keyword: str | None = None
    user_id: UUID | None = None
    is_revoked: bool | None = None
    revoked_by: UUID | None = None
    size: int = 10
    page: int = 1


class UserSessionResponse(BaseSchema):
    id: UUID
    user_id: UUID
    expire_at: datetime | None = None
    user_agent: str | None = None
    user_device: str | None = None
    revoked_at: datetime | None = None
    ipv4: str | None = None
    ipv6: str | None = None


class UpdateUserSession(BaseSchema):
    id: UUID
    user_id: UUID | None = None
    expire_at: datetime | None = None
    user_agent: str | None = None
    user_device: str | None = None
    revoked_at: datetime | None = None
    ipv4: str | None = None
    ipv6: str | None = None
