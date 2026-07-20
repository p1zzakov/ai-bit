from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deep_rest_evidence import collect_deep_rest_evidence

VERSION = "2.0.0-alpha.4"
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


def _source_payloads(artifacts_dir: Path, deep_rest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "deep_rest": deep_rest,
        "crawl": _latest_crawl(artifacts_dir),
        "business_architecture": _read(artifacts_dir / "business-architecture" / "latest.json"),
        "process_mining": _read(artifacts_dir / "process-mining" / "latest.json"),
        "operations": _read(artifacts_dir / "operations" / "latest.json"),
        "capability_discovery": _read(artifacts_dir / "capability-discovery" / "latest.json"),
    }


def _available(source_id: str, payload: dict[str, Any]) -> bool:
    if source_id != "deep_rest":
        return bool(payload)
    summary = payload.get("summary") or {}
    return bool(payload.get("configured")) and int(summary.get("successful_probes") or 0) >= 3


def build_evidence_audit(artifacts_dir: Path) -> dict[str, Any]:
    methodology = _read(METHODOLOGY_PATH)
    discovery = _read(artifacts_dir / "capability-discovery" / "latest.json")
    discovered = discovery.get("capabilities") or {}
    deep_rest = collect_deep_rest_evidence(artifacts_dir)
    deep_capabilities = deep_rest.get("capabilities") or {}
    sources = _source_payloads(artifacts_dir, deep_rest)
    catalog = methodology.get("source_catalog") or {}
    definitions = methodology.get("capabilities") or {}

    capabilities: dict[str, dict[str, Any]] = {}
    for capability_id, definition in definitions.items():
        detected = discovered.get(capability_id) or {}
        rest_detected = deep_capabilities.get(capability_id) or {}
        required = list(definition.get("required_sources") or [])
        usage_sources = set(definition.get("usage_sources") or [])
        checked_sources: list[dict[str, Any]] = []
        positive_sources: list[str] = []
        unavailable_sources: list[str] = []

        for source_id in required:
            payload = sources.get(source_id) or {}
            available = _available(source_id, payload)
            positive = False
            evidence: list[str] = []
            if source_id == "deep_rest" and available:
                positive = bool(rest_detected.get("positive"))
                evidence = list(rest_detected.get("evidence") or [])[:10]
            elif available and detected.get("status") in {"implemented", "partial"}:
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

        all_required_available = bool(required) and not unavailable_sources
        usage_positive = any(source_id in usage_sources for source_id in positive_sources)
        positive_count = len(set(positive_sources))
        rest_positive = "deep_rest" in positive_sources

        if positive_count >= 2 and usage_positive and rest_positive:
            status = "implemented"
            confidence = min(0.98, 0.82 + positive_count * 0.04)
            rationale = "Прямые REST-данные и независимые источники подтверждают конфигурацию и использование."
        elif positive_count >= 1 or detected.get("status") == "partial":
            status = "partial"
            confidence = max(0.58, float(rest_detected.get("confidence") or detected.get("confidence") or 0.58))
            rationale = "Найдены отдельные системные признаки, но полный маршрут или фактическое использование не подтверждены."
        elif all_required_available:
            status = "missing"
            confidence = 0.88
            rationale = "Все обязательные технические источники доступны и проверены; подтверждений процесса не найдено."
        else:
            status = "unknown"
            confidence = 0.35
            rationale = "Недостаточно доступных технических источников для доказательного вывода."

        capabilities[capability_id] = {
            "status": status,
            "confidence": round(confidence, 2),
            "rationale": rationale,
            "required_sources": required,
            "checked_sources": checked_sources,
            "positive_sources": sorted(set(positive_sources)),
            "unavailable_sources": unavailable_sources,
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
        "deep_rest_summary": deep_rest.get("summary", {}),
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
