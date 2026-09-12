from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.services.token_service import TokenService
from app.modules.auth.presentation.schemas.auth_schema import Token
from app.modules.user.infraestructure.repositories.user_repository import UserRepository
from app.modules.user.presentation.schemas.user_schema import SimpleUserResponse
from app.shared.utils.security import verify_password


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)
        self.tokens = TokenService(session)

    async def login(
        self,
        email: str,
        password: str,
        ipv4: str | None = None,
        user_agent: str | None = None,
    ) -> Token:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if user.mfa_enabled:
            return Token(
                access_token=self.tokens.issue_temporary_token(user.id, "mfa"),
                user=SimpleUserResponse.model_validate(user),
                token_role="mfa",
            )
        return await self.tokens.issue_user_token(user, ipv4, user_agent)
