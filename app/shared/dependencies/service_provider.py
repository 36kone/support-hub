from collections.abc import Callable
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infraestructure.database.database import get_db


def get_service(factory: Callable[[AsyncSession], Any]):
    def _get_service(db: AsyncSession = Depends(get_db)):
        return factory(db)

    return _get_service
