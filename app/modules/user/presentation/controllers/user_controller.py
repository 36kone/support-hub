import logging
from typing import Annotated
from uuid import UUID

from app.core.cbv import cbv
from app.dependencies.authentication import auth_guard, required_permissions
from app.dependencies.current_user import CurrentUser
from app.dependencies.rate_limit_route import rate_limited
from app.dependencies.service_provider import get_service
from app.enums import UserRoleEnum
from app.schemas import (
    CreateUser,
    PaginatedResponse,
    UserResponse,
    UserSearchRequest,
    UserUpdate,
)
from app.services.user.factory import build_user_service
from app.services.user.user_service import UserService
from fastapi import APIRouter, Depends, Query

user_router = APIRouter(
    dependencies=[Depends(auth_guard)], route_class=rate_limited("100/minute")
)
logger = logging.getLogger("users")


@cbv(user_router)
class UserController:
    service: UserService = Depends(get_service(build_user_service))

    @user_router.post("/", status_code=201, response_model=UserResponse)
    @required_permissions()
    def create_user(self, data: CreateUser, current_user: CurrentUser):
        try:
            return self.service.create(data, current_user.id)
        except Exception as e:
            logger.exception(f"[CREATE_USER] -> {e}")
            raise

    @user_router.get(
        "/", status_code=200, response_model=PaginatedResponse[UserResponse]
    )
    @required_permissions()
    async def search(self, filters: Annotated[UserSearchRequest, Query()]):
        try:
            return await self.service.search(filters)
        except Exception as e:
            logger.exception(f"[SEARCH_USERS] -> {e}")
            raise

    @user_router.get("/{id_}", status_code=200, response_model=UserResponse)
    @required_permissions()
    def get_user_by_id(self, id_: UUID):
        try:
            return self.service.get_by_id(id_)
        except Exception as e:
            logger.exception(f"[GET_USER_BY_ID] -> {e}")
            raise

    @user_router.put("/{id_}", status_code=200, response_model=UserResponse)
    @required_permissions()
    async def update_user(self, id_: UUID, data: UserUpdate, current_user: CurrentUser):
        try:
            return await self.service.update(id_, data, current_user.id)
        except Exception as e:
            logger.exception(f"[UPDATE_USER] -> {e}")
            raise

    @user_router.delete("/{id_}", status_code=204)
    @required_permissions(roles=[UserRoleEnum.ADMIN])
    def delete_user(self, id_: UUID, current_user: CurrentUser):
        try:
            self.service.delete(id_, current_user.id)
        except Exception as e:
            logger.exception(f"[DELETE_USER] -> {e}")
            raise
