from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.infraestructure.models.user_model import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get(self, user_id: UUID) -> User | None:
        return await self.session.scalar(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(
            select(User).where(User.email == email.lower(), User.deleted_at.is_(None))
        )

    async def get_by_password_reset_token(self, token: str) -> User | None:
        return await self.session.scalar(
            select(User).where(
                User.password_recovery == token,
                User.password_recovery_expire >= datetime.now(UTC),
                User.deleted_at.is_(None),
            )
        )

    async def count(self) -> int:
        return (await self.session.scalar(select(func.count()).select_from(User))) or 0

    async def list(self) -> list[User]:
        return list(
            (await self.session.scalars(select(User).where(User.deleted_at.is_(None)))).all()
        )

    async def search(self, keyword: str | None = None) -> list[User]:
        statement = select(User).where(User.deleted_at.is_(None))
        if keyword:
            value = f"%{keyword.strip()}%"
            statement = statement.where(or_(User.name.ilike(value), User.email.ilike(value)))
        return list((await self.session.scalars(statement.order_by(User.name))).all())
