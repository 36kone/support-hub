from typing import Annotated

from app.dependencies.authentication import get_auth_user
from app.modules.user import User
from fastapi import Depends

CurrentUser = Annotated[User, Depends(get_auth_user)]
