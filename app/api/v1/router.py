from fastapi import APIRouter

from app.modules.auth.presentation.controllers.auth_controller import auth_router
from app.modules.user.presentation.controllers.user_controller import user_router
from app.modules.user.presentation.controllers.user_session_controller import user_session_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(user_session_router, prefix="/user-sessions", tags=["user sessions"])
