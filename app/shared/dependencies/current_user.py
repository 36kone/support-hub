from typing import Annotated

from fastapi import Depends

from app.modules.user.infraestructure.models.user_model import User
from app.shared.dependencies.authentication import get_auth_user

CurrentUser = Annotated[User, Depends(get_auth_user)]
