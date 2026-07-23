from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .base import StorageProvider


class FileSystemStorage(StorageProvider):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, namespace: str, key: str) -> Path:
        safe_namespace = namespace.strip("/\\")
        safe_key = key.strip("/\\")
        if ".." in Path(safe_namespace).parts or ".." in Path(safe_key).parts:
            raise ValueError("Path traversal is not allowed")
        return self.root / safe_namespace / f"{safe_key}.json"

    def write_json(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        target = self._path(namespace, key)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            delete=False,
        ) as handle:
            handle.write(payload)
            temp_name = handle.name
        os.replace(temp_name, target)

    def read_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        target = self._path(namespace, key)
        if not target.exists():
            return None
        return json.loads(target.read_text(encoding="utf-8"))

    def list_keys(self, namespace: str) -> list[str]:
        directory = self.root / namespace.strip("/\\")
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.rglob("*.json"))
