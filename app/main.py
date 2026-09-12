from fastapi import FastAPI

import sys
from pathlib import Path

# Allow both `uv run app/main.py` and `uv run python -m app.main`.
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.v1.health.health_controller import health_router
from app.api.v1.router import api_router
from app.core.config import get_project_version, settings
from app.infraestructure.lifespan.lifespan import lifespan

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_TITLE,
    description=settings.PROJECT_DESCRIPTION,
    version=get_project_version(),
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
)

app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(health_router, prefix="/api/core")

if __name__ == "__main__":
    import sys

    import uvicorn

    debug: bool = False

    # `uv run app/main.py debug` -> aguarda o debugger anexar na porta 5678.
    if "debug" in sys.argv[1:]:
        import debugpy

        debug = True

        debugpy.listen(("0.0.0.0", 5678))
        print("Aguardando o debugger conectar na porta 5678...")
        debugpy.wait_for_client()

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=not debug)
