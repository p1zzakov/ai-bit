from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "2.0.0-alpha.1"
MODEL_PATH = Path(__file__).with_name("reference_models.json")


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _lookup(data: dict[str, Any], dotted: str) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _has_evidence(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return False


def load_reference_model(profile: str | None = None) -> dict[str, Any]:
    model = _read(MODEL_PATH)
    profiles = model.get("profiles") or {}
    selected = profile or os.getenv("REFERENCE_MODEL_PROFILE") or model.get("default_profile")
    current = dict(profiles.get(selected) or {})
    if not current:
        raise ValueError(f"Unknown reference model profile: {selected}")
    inherited = current.get("inherits")
    if inherited:
        base = dict(profiles.get(inherited) or {})
        base.update({k: v for k, v in current.items() if k != "inherits"})
        current = base
    current["id"] = selected
    return current


def build_reference_audit(artifacts_dir: Path, profile: str | None = None) -> dict[str, Any]:
    reference = load_reference_model(profile)
    operations = _read(artifacts_dir / "operations" / "latest.json")
    architecture = _read(artifacts_dir / "business-architecture" / "latest.json")
    mining = _read(artifacts_dir / "process-mining" / "latest.json")
    context = {
        "operations": operations,
        "business_architecture": architecture,
        "process_mining": mining,
    }

    rows: list[dict[str, Any]] = []
    for item in reference.get("capabilities") or []:
        status = str(item.get("forced_status") or "").strip().lower()
        evidence_found: list[str] = []
        if not status:
            for path in item.get("evidence") or []:
                if _has_evidence(_lookup(context, path)):
                    evidence_found.append(path)
            if evidence_found:
                status = "implemented"
            else:
                status = "unknown"
        if status not in {"implemented", "partial", "missing", "unknown"}:
            status = "unknown"
        rows.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "domain": item.get("domain"),
            "weight": float(item.get("weight") or 1),
            "required": bool(item.get("required", True)),
            "status": status,
            "evidence": evidence_found,
        })

    weights = {"implemented": 1.0, "partial": 0.5, "unknown": 0.0, "missing": 0.0}
    total_weight = sum(row["weight"] for row in rows) or 1
    achieved = sum(row["weight"] * weights[row["status"]] for row in rows)
    coverage = round(achieved / total_weight * 100, 1)

    domains: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = domains.setdefault(row["domain"], {"total": 0, "implemented": 0, "partial": 0, "missing": 0, "unknown": 0, "weight": 0.0, "achieved": 0.0})
        bucket["total"] += 1
        bucket[row["status"]] += 1
        bucket["weight"] += row["weight"]
        bucket["achieved"] += row["weight"] * weights[row["status"]]
    for bucket in domains.values():
        bucket["coverage"] = round(bucket["achieved"] / max(bucket["weight"], 1) * 100, 1)
        bucket.pop("achieved", None)
        bucket.pop("weight", None)

    missing = sorted([row for row in rows if row["status"] == "missing"], key=lambda row: row["weight"], reverse=True)
    unknown = sorted([row for row in rows if row["status"] == "unknown"], key=lambda row: row["weight"], reverse=True)
    result = {
        "version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": {"id": reference["id"], "title": reference.get("title"), "description": reference.get("description")},
        "coverage": coverage,
        "summary": {
            "total": len(rows),
            "implemented": sum(1 for row in rows if row["status"] == "implemented"),
            "partial": sum(1 for row in rows if row["status"] == "partial"),
            "missing": len(missing),
            "unknown": len(unknown),
        },
        "domains": domains,
        "capabilities": rows,
        "critical_gaps": missing[:10],
        "requires_verification": unknown[:15],
    }
    folder = artifacts_dir / "reference-audit"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def read_latest_reference_audit(artifacts_dir: Path) -> dict[str, Any]:
    data = _read(artifacts_dir / "reference-audit" / "latest.json")
    if not data:
        raise FileNotFoundError("Reference audit has not been collected")
    return data
