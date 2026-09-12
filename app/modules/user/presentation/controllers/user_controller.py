from fastapi import APIRouter, Depends

from app.modules.user.domain.services.user_service import UserService
from app.modules.user.infraestructure.factories.user_factory import build_user_service
from app.modules.user.presentation.schemas.user_schema import CreateUser, UserResponse
from app.shared.dependencies.current_user import CurrentUser
from app.shared.dependencies.service_provider import get_service
from app.shared.utils.cbv import cbv

user_router = APIRouter()


@cbv(user_router)
class UserController:
    service: UserService = Depends(get_service(build_user_service))

    @user_router.post("/", status_code=201, response_model=UserResponse)
    async def create_user(self, data: CreateUser) -> UserResponse:
        user = await self.service.create(data)
        return UserResponse.model_validate(user)

    @user_router.get("/me", response_model=UserResponse)
    async def current_user(self, current_user: CurrentUser) -> UserResponse:
        return UserResponse.model_validate(current_user)
