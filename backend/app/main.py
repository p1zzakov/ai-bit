from __future__ import annotations

from fastapi import FastAPI

from . import __version__
from .api.router import api_router
from .core.config import get_settings
from .core.lifecycle import lifespan
from .core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    application.include_router(api_router, prefix=settings.api_prefix)

    @application.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.version,
            "status": "platform-core",
        }

    return application


app = create_app()
