from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.domain.services.user_service import UserService


def build_user_service(session: AsyncSession) -> UserService:
    return UserService(session)
