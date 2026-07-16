from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CrawlHistory:
    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, payload: dict[str, Any]) -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = self.root / f"crawl-{stamp}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("crawl-*.json"), reverse=True)[:limit]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            rows.append(
                {
                    "id": path.stem,
                    "created_at": data.get("generated_at") or path.stem.removeprefix("crawl-"),
                    "summary": data.get("summary", {}),
                    "path": str(path),
                }
            )
        return rows

    def read(self, audit_id: str) -> dict[str, Any]:
        path = self.root / f"{audit_id}.json"
        if not path.exists():
            raise FileNotFoundError(audit_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def latest(self) -> dict[str, Any]:
        items = self.list(limit=1)
        if not items:
            raise FileNotFoundError("No crawl history")
        return self.read(items[0]["id"])


def _node_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for node in payload.get("nodes", []):
        url = str(node.get("url", "")).rstrip("/")
        if url:
            result[url] = node
    return result


def diff_crawls(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    old = _node_index(before)
    new = _node_index(after)

    added_urls = sorted(set(new) - set(old))
    removed_urls = sorted(set(old) - set(new))
    changed: list[dict[str, Any]] = []

    for url in sorted(set(old) & set(new)):
        previous = old[url]
        current = new[url]
        fields: dict[str, dict[str, Any]] = {}
        for key in ("title", "status", "section", "http_status"):
            if previous.get(key) != current.get(key):
                fields[key] = {"before": previous.get(key), "after": current.get(key)}
        if fields:
            changed.append({"url": url, "changes": fields})

    section_before = before.get("summary", {}).get("sections", {})
    section_after = after.get("summary", {}).get("sections", {})
    sections = sorted(set(section_before) | set(section_after))
    section_delta = {
        section: int(section_after.get(section, 0)) - int(section_before.get(section, 0))
        for section in sections
        if int(section_after.get(section, 0)) != int(section_before.get(section, 0))
    }

    return {
        "before_generated_at": before.get("generated_at"),
        "after_generated_at": after.get("generated_at"),
        "summary": {
            "added": len(added_urls),
            "removed": len(removed_urls),
            "changed": len(changed),
            "section_delta": section_delta,
        },
        "added": [new[url] for url in added_urls],
        "removed": [old[url] for url in removed_urls],
        "changed": changed,
    }
