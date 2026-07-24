from __future__ import annotations

from functools import lru_cache

from .core.config import get_settings
from .plugins.registry import PluginRegistry
from .storage.filesystem import FileSystemStorage


@lru_cache(maxsize=1)
def get_storage() -> FileSystemStorage:
    return FileSystemStorage(get_settings().storage_root)


@lru_cache(maxsize=1)
def get_plugin_registry() -> PluginRegistry:
    return PluginRegistry()
