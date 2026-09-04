import logging
from uuid import UUID

from app.core.exception_utils import (
    ensure_400,
    ensure_or_400,
    ensure_or_404,
)
from app.core.security import get_password_hash, verify_password
from app.models import Customer, User
from app.repositories import CustomerRepository, UserRepository
from app.schemas import (
    CreateAuditLog,
    CreateUser,
    CurrentUserUpdate,
    PaginatedResponse,
    UserResponse,
    UserSearchRequest,
    UserUpdate,
)
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from sqlalchemy.orm import Session as DBSession

from ...enums import AuditLogActionEnum
from ..logs.audit_log_service import AuditLogService
from ..user.user_session_service import UserSessionService

logger = logging.getLogger("user-service")


class UserService:
    def __init__(
        self,
        session: DBSession,
        repository: UserRepository,
        customer_repository: CustomerRepository,
        user_session_service: UserSessionService,
        audit_log_service: AuditLogService,
    ):
        self._session = session
        self._repository = repository
        self._customer_repository = customer_repository
        self._user_session_service = user_session_service
        self._audit_log_service = audit_log_service

    def _validate_user_data(
        self,
        email: str | None = None,
        phone: str | None = None,
        customer_id: UUID | None = None,
        username: str | None = None,
        id_: UUID | None = None,
    ) -> None:
        if phone is not None and self._repository.exists_by_phone(phone, id_):
            raise HTTPException(status_code=400, detail="Phone already exists")
        if email is not None and self._repository.exists_by_email(email, id_):
            raise HTTPException(status_code=400, detail="Email already exists")

    def _get_customer_by_id(self, customer_id: UUID) -> Customer:
        return ensure_or_404(self._customer_repository.get(customer_id, options=[]))

    def create(self, data: CreateUser, current_user_id: UUID) -> User:
        self._validate_user_data(
            email=str(data.email),
            phone=data.phone,
            customer_id=data.customer_id,
            username=data.username,
        )

        entity = User(
            created_by=current_user_id,
            name=data.name,
            email=str(data.email).strip(),
            password=get_password_hash(data.password.strip()),
            phone=data.phone,
            role=data.role,
            single_session=data.single_session,
            allow_virtual_agent=data.allow_virtual_agent,
            mfa_enabled=data.mfa_enabled,
            is_super_user=data.is_super_user,
        )

        self._repository.add(entity)
        self._session.commit()

        self._audit_log_service.create(
            data=CreateAuditLog(
                user_id=current_user_id,
                entity="auth.users",
                object_id=entity.id,
                after=jsonable_encoder(self.get_by_id(entity.id)),
                action=AuditLogActionEnum.CREATE,
            )
        )

        return self.get_by_id(entity.id)

    async def search(
        self, filters: UserSearchRequest
    ) -> PaginatedResponse[UserResponse]:
        items, total = self._repository.search(filters)

        return PaginatedResponse.create(
            total=total,
            page=filters.page,
            size=filters.size,
            items=[UserResponse.model_validate(i, from_attributes=True) for i in items],
        )

    def get_by_id(self, id_: UUID) -> User:
        return ensure_or_404(
            self._repository.get(id_),
            "User not found",
        )

    def get_by_customer_id(self, customer_id: UUID) -> User | None:
        return self._repository.get_by_customer_id(customer_id)

    def get_by_email(self, email: EmailStr) -> User | None:
        return self._repository.get_by_email(str(email))

    def get_by_username(self, username: str) -> User | None:
        return self._repository.get_by_username(username)

    async def get_by_password_reset_token(self, token: str) -> User | None:
        return ensure_or_404(
            self._repository.get_by_password_reset_token(token),
            "Not a valid token or expired",
        )

    def verify_by_password(self, password: str, id_: UUID) -> bool:
        user = self.get_by_id(id_)

        ensure_400(user is None, "Incorrect email or password.")
        ensure_or_400(
            verify_password(password, user.password),
            "Invalid credentials.",
        )
        return True

    async def update(self, id_: UUID, data: UserUpdate, current_user_id: UUID) -> User:
        entity = self.get_by_id(id_)

        before = UserResponse.model_validate(entity)

        self._validate_user_data(
            email=data.email,
            phone=data.phone,
            customer_id=data.customer_id,
            username=data.username,
            id_=id_,
        )

        if data.mfa_enabled is False:
            entity.mfa_enabled = False
            entity.mfa_secret = None
        elif data.mfa_enabled:
            await self._user_session_service.revoke_user_sessions(entity.id)

        try:
            data_dict = data.model_dump(exclude_unset=True)

            for field, value in data_dict.items():
                setattr(entity, field, value)

            entity.updated_by = current_user_id

            self._repository.add(entity)
            self._session.commit()

            updated_entity = self.get_by_id(entity.id)

            await self._user_session_service.invalidate_user_cache(entity.id)

            after = UserResponse.model_validate(updated_entity)

            self._audit_log_service.create(
                data=CreateAuditLog(
                    user_id=current_user_id,
                    entity="auth.users",
                    object_id=entity.id,
                    before=before.model_dump(mode="json"),
                    after=after.model_dump(mode="json"),
                    action=AuditLogActionEnum.UPDATE,
                )
            )

            return updated_entity

        except Exception as error:
            logger.exception(f"[USER UPDATE] FAILED -> {error}")
            self._session.rollback()
            raise HTTPException(status_code=400, detail="Update failed") from error

    async def update_current_user(
        self, data: CurrentUserUpdate, current_user_id: UUID
    ) -> User:
        return await self.update(
            id_=current_user_id,
            current_user_id=current_user_id,
            data=UserUpdate(
                name=data.name,
                email=data.email,
                phone=data.phone,
            ),
        )

    def delete(self, id_: UUID, current_user_id: UUID) -> None:
        entity = self.get_by_id(id_)

        if entity.deleted_at is not None:
            raise HTTPException(404, "Not found")

        self._repository.soft_delete(entity)
        self._session.commit()

        self._audit_log_service.create(
            data=CreateAuditLog(
                user_id=current_user_id,
                entity="auth.users",
                object_id=entity.id,
                after=jsonable_encoder(entity),
                action=AuditLogActionEnum.DELETE,
            )
        )
