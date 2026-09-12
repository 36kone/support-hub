from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.services.token_service import TokenService


def build_token_service(session: AsyncSession) -> TokenService:
    return TokenService(session)
