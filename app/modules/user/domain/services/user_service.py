from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.infraestructure.models.user_model import User
from app.modules.user.infraestructure.repositories.user_repository import UserRepository
from app.modules.user.presentation.schemas.user_schema import CreateUser
from app.shared.utils.security import get_password_hash


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def create(self, data: CreateUser, creator_id=None) -> User:
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
