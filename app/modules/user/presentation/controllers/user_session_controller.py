import logging
from typing import Annotated
from uuid import UUID

from app.core.cbv import cbv
from app.dependencies.authentication import (
    auth_guard,
    get_token_payload,
    required_permissions,
)
from app.dependencies.current_user import CurrentUser
from app.dependencies.service_provider import get_service
from app.schemas import (
    PaginatedResponse,
    UserSessionResponse,
    UserSessionSearchRequest,
)
from app.services.user.factory import build_user_session_service
from app.services.user.user_session_service import UserSessionService
from fastapi import APIRouter, Depends, HTTPException, Query

user_session_router = APIRouter(dependencies=[Depends(auth_guard)])
logger = logging.getLogger(__name__)


@cbv(user_session_router)
class UserSessionController:
    service: UserSessionService = Depends(get_service(build_user_session_service))

    @user_session_router.put("/revoke-current-session", status_code=204)
    @required_permissions()
    async def revoke_current_user_session(
        self,
        payload: dict = Depends(get_token_payload),
    ):
        try:
            session_id = payload.get("sid")

            if not session_id:
                raise HTTPException(
                    status_code=401,
                    detail="Could not validate credentials",
                )

            await self.service.revoke_session(UUID(session_id))
        except Exception as e:
            logger.exception(f"[REVOKE_CURRENT_USER_SESSION] -> {e}")
            raise

    @user_session_router.put("/revoke/{id_}", status_code=204)
    @required_permissions()
    async def revoke_user_session_by_id(
        self,
        id_: UUID,
        current_user: CurrentUser,
    ):
        try:
            self.service.get_by_id(id_)

            await self.service.revoke_session(id_, current_user.id)
        except Exception as e:
            logger.exception(f"[REVOKE_USER_SESSION_BY_ID] -> {e}")
            raise

    @user_session_router.get(
        "/", status_code=200, response_model=PaginatedResponse[UserSessionResponse]
    )
    @required_permissions()
    async def search_sessions(
        self, filters: Annotated[UserSessionSearchRequest, Query()]
    ):
        try:
            return await self.service.search(filters)
        except Exception as e:
            logger.exception(f"[SEARCH_USER_SESSIONS] -> {e}")
            raise
