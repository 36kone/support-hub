from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.domain.services.user_session_service import UserSessionService


def build_user_session_service(session: AsyncSession) -> UserSessionService:
    return UserSessionService(session)
