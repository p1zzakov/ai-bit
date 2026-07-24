from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from ..dependencies import get_plugin_registry, get_storage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    storage = get_storage()
    registry = get_plugin_registry()
    app.state.storage = storage
    app.state.plugins = registry
    logger.info("AI-BIT platform core started")
    yield
    logger.info("AI-BIT platform core stopped")
