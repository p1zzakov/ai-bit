from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


_SAFE = re.compile(r"[^a-zA-Z0-9_.-]+")


def safe_name(value: str) -> str:
    cleaned = _SAFE.sub("_", value.strip())
    return cleaned[:128] or "unknown"


class DiscoveryRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.snapshots_dir = root / "snapshots"
        self.index_dir = root / "index"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def _snapshot_path(self, agent_id: str, fingerprint: str) -> Path:
        return self.snapshots_dir / safe_name(agent_id) / f"{fingerprint}.json"

    def exists(self, agent_id: str, fingerprint: str) -> bool:
        return self._snapshot_path(agent_id, fingerprint).exists()

    def store(self, agent_id: str, document: dict[str, Any]) -> tuple[Path, str]:
        fingerprint = str(document["fingerprint"]).lower()
        target = self._snapshot_path(agent_id, fingerprint)
        target.parent.mkdir(parents=True, exist_ok=True)
        stored_at = datetime.now(UTC).isoformat()
        persisted = {**document, "ingestion": {"agent_id": agent_id, "stored_at_utc": stored_at}}
        payload = json.dumps(persisted, ensure_ascii=False, indent=2).encode("utf-8")
        fd, temp_name = tempfile.mkstemp(prefix="snapshot-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        self._append_index(agent_id, persisted)
        return target, stored_at

    def _append_index(self, agent_id: str, document: dict[str, Any]) -> None:
        payload = document.get("payload", {})
        collectors = payload.get("collectors", [])
        statuses: dict[str, int] = {}
        for collector in collectors:
            status = str(collector.get("status", "unknown"))
            statuses[status] = statuses.get(status, 0) + 1
        record = {
            "agent_id": agent_id,
            "snapshot_id": payload.get("snapshot_id"),
            "fingerprint": document.get("fingerprint"),
            "collected_at_utc": payload.get("collected_at_utc"),
            "stored_at_utc": document.get("ingestion", {}).get("stored_at_utc"),
            "schema_version": payload.get("schema_version"),
            "agent_version": payload.get("agent_version"),
            "collector_statuses": statuses,
        }
        index_path = self.index_dir / f"{safe_name(agent_id)}.jsonl"
        with index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    def list_snapshots(self, agent_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        paths = [self.index_dir / f"{safe_name(agent_id)}.jsonl"] if agent_id else sorted(self.index_dir.glob("*.jsonl"))
        records: list[dict[str, Any]] = []
        for path in paths:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    records.append(json.loads(line))
        records.sort(key=lambda item: item.get("stored_at_utc") or "", reverse=True)
        return records[:limit]

    def read(self, agent_id: str, fingerprint: str) -> dict[str, Any] | None:
        path = self._snapshot_path(agent_id, fingerprint.lower())
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
