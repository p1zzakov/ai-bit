from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageProvider(ABC):
    @abstractmethod
    def write_json(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def list_keys(self, namespace: str) -> list[str]:
        raise NotImplementedError
