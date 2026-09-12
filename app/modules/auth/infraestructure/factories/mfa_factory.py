from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.services.mfa_service import MfaService


def build_mfa_service(session: AsyncSession) -> MfaService:
    return MfaService(session)
