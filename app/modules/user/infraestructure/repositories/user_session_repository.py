from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.infraestructure.models.user_session_model import UserSession


class UserSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_session: UserSession) -> UserSession:
        self.session.add(user_session)
        await self.session.flush()
        return user_session

    async def get_active(self, session_id: UUID, user_id: UUID) -> UserSession | None:
        return await self.session.scalar(
            select(UserSession).where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expire_at > datetime.now(UTC),
            )
        )

    async def get(self, session_id: UUID) -> UserSession | None:
        return await self.session.get(UserSession, session_id)

    async def get_by_user_id(self, user_id: UUID) -> UserSession | None:
        return await self.session.scalar(
            select(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .order_by(UserSession.created_at.desc())
        )

    async def list_by_user(self, user_id: UUID) -> list[UserSession]:
        return list(
            (
                await self.session.scalars(
                    select(UserSession)
                    .where(UserSession.user_id == user_id)
                    .order_by(UserSession.created_at.desc())
                )
            ).all()
        )

    async def revoke(self, session_id: UUID, user_id: UUID) -> bool:
        session = await self.get_active(session_id, user_id)
        if session is None:
            return False
        session.revoked_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        sessions = await self.list_by_user(user_id)
        now = datetime.now(UTC)
        for session in sessions:
            if session.revoked_at is None:
                session.revoked_at = now
        await self.session.flush()
