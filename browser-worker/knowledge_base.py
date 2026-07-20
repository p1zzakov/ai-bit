from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VERSION = "2.0.0-alpha.5"
CATALOG_PATH = Path(__file__).with_name("knowledge_catalog.json")


def _read() -> dict[str, Any]:
    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": VERSION, "modules": {}}


def get_catalog() -> dict[str, Any]:
    return _read()


def get_module(capability_id: str) -> dict[str, Any]:
    catalog = _read()
    module = dict((catalog.get("modules") or {}).get(capability_id) or {})
    if not module:
        raise KeyError(capability_id)
    module["id"] = capability_id
    module["knowledge_version"] = catalog.get("version", VERSION)
    module["disclaimer"] = catalog.get("disclaimer")
    return module


def enrich_capability(capability: dict[str, Any]) -> dict[str, Any]:
    row = dict(capability)
    capability_id = str(row.get("id") or "")
    knowledge = (get_catalog().get("modules") or {}).get(capability_id) or {}
    status = str(row.get("status") or "unknown")
    recommendations = knowledge.get("recommendations") or {}
    row["methodology"] = {
        "title": knowledge.get("title") or row.get("title"),
        "objective": knowledge.get("objective"),
        "best_practices": knowledge.get("best_practices") or [],
        "anti_patterns": knowledge.get("anti_patterns") or [],
        "evidence_requirements": knowledge.get("evidence_requirements") or [],
        "recommendation": recommendations.get(status) or recommendations.get("partial"),
        "knowledge_version": get_catalog().get("version", VERSION),
    }
    return row


def enrich_reference_audit(result: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(result)
    rows = [enrich_capability(row) for row in result.get("capabilities") or []]
    enriched["capabilities"] = rows
    by_id = {str(row.get("id")): row for row in rows}
    enriched["critical_gaps"] = [by_id.get(str(row.get("id")), row) for row in result.get("critical_gaps") or []]
    enriched["requires_verification"] = [by_id.get(str(row.get("id")), row) for row in result.get("requires_verification") or []]
    enriched["knowledge_base"] = {
        "version": get_catalog().get("version", VERSION),
        "title": get_catalog().get("title"),
        "modules": len(get_catalog().get("modules") or {}),
        "disclaimer": get_catalog().get("disclaimer"),
    }
    return enriched
