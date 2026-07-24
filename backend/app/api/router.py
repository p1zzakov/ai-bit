from __future__ import annotations

from fastapi import APIRouter

from .browser import router as browser_router
from .discovery import router as discovery_router
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/system")
api_router.include_router(discovery_router)
api_router.include_router(browser_router)
