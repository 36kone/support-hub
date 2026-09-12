from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infraestructure.database.database import get_db
from app.modules.user.domain.services.user_service import UserService
from app.modules.user.presentation.schemas.user_schema import CreateUser, UserResponse
from app.shared.dependencies.current_user import CurrentUser

user_router = APIRouter()


@user_router.post("", status_code=201, response_model=UserResponse)
async def create_user(data: CreateUser, session: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await UserService(session).create(data)
    return UserResponse.model_validate(user)


@user_router.get("/me", response_model=UserResponse)
async def current_user(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
