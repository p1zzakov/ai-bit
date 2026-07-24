from __future__ import annotations

from collections.abc import Iterable

from .base import PlatformPlugin


class PluginRegistry:
    def __init__(self, plugins: Iterable[PlatformPlugin] = ()) -> None:
        self._plugins: dict[str, PlatformPlugin] = {}
        for plugin in plugins:
            self.register(plugin)

    def register(self, plugin: PlatformPlugin) -> None:
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"Plugin already registered: {name}")
        self._plugins[name] = plugin

    def list(self) -> list[PlatformPlugin]:
        return [self._plugins[name] for name in sorted(self._plugins)]

    def health(self) -> list[dict[str, object]]:
        return [
            {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "capabilities": list(plugin.metadata.capabilities),
                "health": plugin.health(),
            }
            for plugin in self.list()
        ]
