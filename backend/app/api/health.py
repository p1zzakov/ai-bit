from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.config import Settings, get_settings
from ..dependencies import get_plugin_registry
from ..plugins.registry import PluginRegistry

router = APIRouter(tags=["system"])


@router.get("/health")
def health(
    settings: Settings = Depends(get_settings),
    registry: PluginRegistry = Depends(get_plugin_registry),
) -> dict[str, object]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "plugins": registry.health(),
    }


@router.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}
