from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import redis.asyncio as redis
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.user.infraestructure.models.user_model import User
from app.modules.user.infraestructure.models.user_session_model import UserSession
from app.modules.user.infraestructure.repositories.user_session_repository import (
    UserSessionRepository,
)
from app.modules.user.presentation.schemas.user_session_schema import (
    UpdateUserSession,
    UserSessionSearchRequest,
)


class UserSessionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.sessions = UserSessionRepository(session)

    async def list_by_user(self, user_id: UUID) -> list[UserSession]:
        return await self.sessions.list_by_user(user_id)

    async def create_user_session(
        self,
        user: User,
        ipv4: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        if user.single_session:
            await self.sessions.revoke_all_for_user(user.id)
        user_session = UserSession(
            id=uuid4(),
            user_id=user.id,
            expire_at=datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE),
            ipv4=ipv4,
            user_agent=user_agent,
        )
        await self.sessions.create(user_session)
        await self.session.commit()
        return user_session

    async def get_by_id(self, id_: UUID) -> UserSession:
        user_session = await self.sessions.get(id_)
        if user_session is None:
            raise HTTPException(status_code=404, detail="User session not found")
        return user_session

    async def get_push_token_by_user_id(self, user_id: UUID) -> str | None:
        # Push tokens are not part of the current session model.
        return None

    async def get_by_user_id(self, user_id: UUID) -> UserSession | None:
        return await self.sessions.get_by_user_id(user_id)

    async def search(self, filters: UserSessionSearchRequest) -> list[UserSession]:
        if filters.user_id is None:
            return []
        return await self.sessions.list_by_user(filters.user_id)

    async def update(self, data: UpdateUserSession) -> UserSession:
        user_session = await self.get_by_id(data.id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if field != "id" and hasattr(user_session, field):
                setattr(user_session, field, value)
        await self.session.commit()
        await self.session.refresh(user_session)
        return user_session

    async def revoke(self, session_id: UUID, user_id: UUID) -> None:
        if not await self.sessions.revoke(session_id, user_id):
            raise HTTPException(status_code=401, detail="Session is no longer valid")
        await self.session.commit()
        cache = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        try:
            await cache.delete(f"auth:session:{session_id}:user:{user_id}")
        finally:
            await cache.aclose()

    async def revoke_session(self, id_: UUID, current_user_id: UUID | None = None) -> None:
        user_session = await self.get_by_id(id_)
        if not await self.sessions.revoke(id_, user_session.user_id):
            raise HTTPException(status_code=401, detail="Session is no longer valid")
        await self.session.commit()

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        # Session validation currently reads PostgreSQL directly; no cache to invalidate.
        return None

    async def revoke_user_sessions(self, user_id: UUID) -> None:
        await self.sessions.revoke_all_for_user(user_id)
        await self.session.commit()
