from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "2.0.0-alpha.3"
METHODOLOGY_PATH = Path(__file__).with_name("evidence_methodology.json")


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _latest_crawl(artifacts_dir: Path) -> dict[str, Any]:
    for path in sorted((artifacts_dir / "history").glob("*.json"), reverse=True):
        data = _read(path)
        if data:
            return data
    return {}


def _source_payloads(artifacts_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        "crawl": _latest_crawl(artifacts_dir),
        "business_architecture": _read(artifacts_dir / "business-architecture" / "latest.json"),
        "process_mining": _read(artifacts_dir / "process-mining" / "latest.json"),
        "operations": _read(artifacts_dir / "operations" / "latest.json"),
        "capability_discovery": _read(artifacts_dir / "capability-discovery" / "latest.json"),
    }


def build_evidence_audit(artifacts_dir: Path) -> dict[str, Any]:
    methodology = _read(METHODOLOGY_PATH)
    discovery = _read(artifacts_dir / "capability-discovery" / "latest.json")
    discovered = discovery.get("capabilities") or {}
    sources = _source_payloads(artifacts_dir)
    catalog = methodology.get("source_catalog") or {}
    definitions = methodology.get("capabilities") or {}

    capabilities: dict[str, dict[str, Any]] = {}
    for capability_id, definition in definitions.items():
        detected = discovered.get(capability_id) or {}
        required = list(definition.get("required_sources") or [])
        usage_sources = set(definition.get("usage_sources") or [])
        checked_sources: list[dict[str, Any]] = []
        positive_sources: list[str] = []
        unavailable_sources: list[str] = []

        for source_id in required:
            available = bool(sources.get(source_id))
            positive = False
            evidence: list[str] = []
            if source_id == "capability_discovery":
                available = bool(discovery)
            if available and detected.get("status") in {"implemented", "partial"}:
                detected_source = str(detected.get("source") or "")
                # Current discovery is built from all available artifacts. We preserve
                # the source inventory and do not pretend that one regex match proves
                # activity in every source independently.
                if source_id in {"crawl", "business_architecture", "process_mining", "operations"}:
                    evidence = list(detected.get("evidence") or [])[:8]
                    positive = bool(evidence)
            if positive:
                positive_sources.append(source_id)
            if not available:
                unavailable_sources.append(source_id)
            checked_sources.append({
                "id": source_id,
                "title": (catalog.get(source_id) or {}).get("title", source_id),
                "available": available,
                "positive": positive,
                "evidence": evidence,
                "usage_source": source_id in usage_sources,
            })

        manual_claim = definition.get("manual_claim")
        if manual_claim:
            checked_sources.append({
                "id": "manual_claim",
                "title": (catalog.get("manual_claim") or {}).get("title", "Подтверждение владельца процесса"),
                "available": True,
                "positive": manual_claim == "implemented",
                "evidence": [f"Заявленный статус: {manual_claim}"],
                "usage_source": False,
            })

        all_required_available = bool(required) and not unavailable_sources
        usage_positive = any(source_id in usage_sources for source_id in positive_sources)
        positive_count = len(set(positive_sources))

        if positive_count >= 2 and usage_positive:
            status = "implemented"
            confidence = min(0.98, 0.78 + positive_count * 0.06)
            rationale = "Найдены независимые подтверждения конфигурации и фактического использования."
        elif positive_count >= 1 or detected.get("status") == "partial":
            status = "partial"
            confidence = max(0.55, float(detected.get("confidence") or 0.55))
            rationale = "Найдены отдельные признаки процесса, но полный маршрут или фактическое использование не подтверждены."
        elif all_required_available:
            status = "missing"
            confidence = 0.9 if manual_claim == "not_implemented" else 0.82
            rationale = "Все обязательные источники доступны и проверены; подтверждений процесса не найдено."
        else:
            status = "unknown"
            confidence = 0.35
            rationale = "Недостаточно доступных источников для доказательного вывода."

        capabilities[capability_id] = {
            "status": status,
            "confidence": round(confidence, 2),
            "rationale": rationale,
            "required_sources": required,
            "checked_sources": checked_sources,
            "positive_sources": sorted(set(positive_sources)),
            "unavailable_sources": unavailable_sources,
            "manual_claim": manual_claim,
            "methodology_version": methodology.get("version"),
        }

    result = {
        "version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "methodology": {
            "title": methodology.get("title"),
            "version": methodology.get("version"),
            "description": methodology.get("description"),
            "status_rules": methodology.get("status_rules"),
        },
        "capabilities": capabilities,
        "summary": {
            "implemented": sum(1 for row in capabilities.values() if row["status"] == "implemented"),
            "partial": sum(1 for row in capabilities.values() if row["status"] == "partial"),
            "missing": sum(1 for row in capabilities.values() if row["status"] == "missing"),
            "unknown": sum(1 for row in capabilities.values() if row["status"] == "unknown"),
        },
    }
    folder = artifacts_dir / "evidence-audit"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def read_latest_evidence_audit(artifacts_dir: Path) -> dict[str, Any]:
    data = _read(artifacts_dir / "evidence-audit" / "latest.json")
    if not data:
        raise FileNotFoundError("Evidence audit has not been collected")
    return data
