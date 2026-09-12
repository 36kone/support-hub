from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.infraestructure.models.user_model import User
from app.modules.user.infraestructure.repositories.user_repository import UserRepository
from app.modules.user.presentation.schemas.user_schema import (
    CreateUser,
    UpdateCurrentUser,
    UpdateUser,
    UserSearchRequest,
)
from app.shared.utils.security import get_password_hash, verify_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def _validate_user_data(self, email: str | None = None, id_: UUID | None = None) -> None:
        if email is None:
            return
        existing = await self.users.get_by_email(email)
        if existing is not None and existing.id != id_:
            raise HTTPException(status_code=409, detail="Email already registered")

    async def create(self, data: CreateUser, creator_id: UUID | None = None) -> User:
        if await self.users.get_by_email(str(data.email)):
            raise HTTPException(status_code=409, detail="Email already registered")
        user = User(
            name=data.name,
            email=str(data.email).lower(),
            password=get_password_hash(data.password),
            phone=data.phone,
            single_session=data.single_session,
            mfa_enabled=data.mfa_enabled,
            is_super_user=data.is_super_user,
            created_by=creator_id,
        )
        await self.users.create(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def search(self, filters: UserSearchRequest) -> list[User]:
        return await self.users.search(filters.keyword)

    async def get_by_id(self, id_: UUID) -> User:
        user = await self.users.get(id_)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.users.get_by_email(email)

    async def get_by_username(self, username: str) -> User | None:
        # The current user model does not expose usernames yet.
        return None

    async def get_by_password_reset_token(self, token: str) -> User:
        user = await self.users.get_by_password_reset_token(token)
        if user is None:
            raise HTTPException(status_code=404, detail="Not a valid token or expired")
        return user

    async def verify_by_password(self, password: str, id_: UUID) -> bool:
        user = await self.get_by_id(id_)
        if not verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        return True

    async def update(self, id_: UUID, data: UpdateUser, current_user_id: UUID) -> User:
        user = await self.get_by_id(id_)
        values = data.model_dump(exclude_unset=True)
        if email := values.get("email"):
            await self._validate_user_data(email, id_)
            values["email"] = str(email).lower()
        for field, value in values.items():
            setattr(user, field, value)
        user.updated_by = current_user_id
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_current_user(self, data: UpdateCurrentUser, current_user_id: UUID) -> User:
        return await self.update(
            current_user_id,
            UpdateUser(name=data.name, email=data.email, phone=data.phone),
            current_user_id,
        )

    async def delete(self, id_: UUID, current_user_id: UUID) -> None:
        user = await self.get_by_id(id_)
        user.deleted_at = datetime.now(UTC)
        user.updated_by = current_user_id
        await self.session.commit()
