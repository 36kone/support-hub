from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.services.password_service import PasswordService


def build_password_service(session: AsyncSession) -> PasswordService:
    return PasswordService(session)
