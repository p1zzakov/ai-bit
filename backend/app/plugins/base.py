from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    name: str
    version: str
    capabilities: tuple[str, ...]


class PlatformPlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict[str, Any]:
        raise NotImplementedError
