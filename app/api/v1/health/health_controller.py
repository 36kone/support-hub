from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.infraestructure.database.database import get_db

health_router = APIRouter()


@health_router.get("/health")
async def health_check() -> dict:
    try:
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            break
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"message": "Database unavailable", "databaseAlive": False},
        )
    return {"message": "Core Running OK", "databaseAlive": True}
