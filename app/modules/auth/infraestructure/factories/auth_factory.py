from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.services.auth_service import AuthService


def build_auth_service(session: AsyncSession) -> AuthService:
    return AuthService(session)
