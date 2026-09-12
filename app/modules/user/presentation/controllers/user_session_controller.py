from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.modules.user.domain.services.user_session_service import UserSessionService
from app.modules.user.infraestructure.factories.user_session_factory import (
    build_user_session_service,
)
from app.modules.user.presentation.schemas.user_session_schema import UserSessionResponse
from app.shared.dependencies.authentication import bearer_scheme
from app.shared.dependencies.current_user import CurrentUser
from app.shared.dependencies.service_provider import get_service
from app.shared.utils.cbv import cbv
from app.shared.utils.security import decode_access_token

user_session_router = APIRouter()


@cbv(user_session_router)
class UserSessionController:
    service: UserSessionService = Depends(get_service(build_user_session_service))

    @user_session_router.get("/", response_model=list[UserSessionResponse])
    async def list_sessions(
        self,
        current_user: CurrentUser,
    ):
        return await self.service.list_by_user(current_user.id)

    @user_session_router.delete("/current", status_code=204)
    async def revoke_current_session(
        self,
        current_user: CurrentUser,
        credentials=Depends(bearer_scheme),
    ) -> None:
        payload = decode_access_token(credentials.credentials)
        session_id = UUID(payload["sid"]) if payload else None
        if session_id is None:
            raise HTTPException(status_code=401, detail="Session is no longer valid")
        await self.service.revoke(session_id, current_user.id)
