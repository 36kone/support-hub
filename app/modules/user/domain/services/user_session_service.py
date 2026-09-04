import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.exception_utils import ensure_or_404
from app.models import User, UserSession
from app.redis.redis import redis_client
from app.repositories import UserSessionRepository
from app.schemas import (
    PaginatedResponse,
    UserSessionResponse,
    UserSessionSearchRequest,
    UserSessionUpdate,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings


class UserSessionService:
    def __init__(self, session: Session, repository: UserSessionRepository):
        self._session = session
        self._repository = repository

    async def create_user_session(
        self,
        user: User,
        ipv4: str | None = None,
        user_agent: str | None = None,
    ):
        if user and user.single_session:
            await self.revoke_user_sessions(user.id)

        user_session = UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            expire_at=datetime.now(UTC)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE),
            user_agent=user_agent,
            ipv4=ipv4,
        )

        self._repository.add(user_session)
        self._session.commit()

        return user_session

    def get_by_id(self, id_: UUID):
        return ensure_or_404(
            self._repository.get(id_),
            "User session not found",
        )

    def get_push_token_by_user_id(self, user_id: UUID) -> str | None:
        return self._repository.get_push_token_by_user_id(user_id)

    def get_by_user_id(self, user_id: UUID):
        return self._repository.get_by_user_id(user_id)

    async def search(
        self, filters: UserSessionSearchRequest
    ) -> PaginatedResponse[UserSessionResponse]:
        items, total = self._repository.search(filters)

        return PaginatedResponse.create(
            total=total,
            page=filters.page,
            size=filters.size,
            items=[
                UserSessionResponse.model_validate(i, from_attributes=True)
                for i in items
            ],
        )

    def update(self, data: UserSessionUpdate):
        entity = self.get_by_id(data.id)

        try:
            data_dict = data.model_dump(exclude_unset=True)

            for field, value in data_dict.items():
                setattr(entity, field, value)

            self._session.commit()
            return entity

        except HTTPException as error:
            self._session.rollback()
            raise HTTPException(
                status_code=400, detail=f"Update failed - {error}"
            ) from error

    async def revoke_session(
        self, id_: UUID, current_user_id: UUID | None = None
    ) -> None:
        session = self._repository.get(id_)

        self._repository.revoke(id_, current_user_id)
        self._session.commit()

        if session:
            redis = await redis_client.get_client()
            await redis.delete(f"auth:session:{id_}:user:{session.user_id}")

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        session_ids = self._repository.get_active_ids_by_user_id(user_id)

        if session_ids:
            redis = await redis_client.get_client()
            await redis.delete(
                *(f"auth:session:{sid}:user:{user_id}" for sid in session_ids)
            )

    async def revoke_user_sessions(self, user_id: UUID) -> None:
        revoked_ids = self._repository.revoke_by_user_id(user_id)
        self._session.commit()

        if revoked_ids:
            redis = await redis_client.get_client()
            await redis.delete(
                *(f"auth:session:{sid}:user:{user_id}" for sid in revoked_ids)
            )
