from collections.abc import Callable
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infraestructure.database.database import get_db


def get_service(factory: Callable[[Session], Any]):
    def _get_service(db: Session = Depends(get_db)):
        return factory(db)

    return _get_service
