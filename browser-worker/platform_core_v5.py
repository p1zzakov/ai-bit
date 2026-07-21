from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

VERSION = "5.0.0"


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return sha256(_stable(value).encode("utf-8")).hexdigest()


def _confidence(evidence_count: int, confirmed: bool, contradictory: bool = False) -> float:
    score = 0.35 + min(evidence_count, 5) * 0.12
    if confirmed:
        score += 0.15
    if contradictory:
        score -= 0.25
    return round(max(0.05, min(0.99, score)), 2)


def _evidence_engine(pipeline: dict[str, Any]) -> dict[str, Any]:
    assessment = pipeline.get("best_practice_assessment") or {}
    findings = assessment.get("confirmed_findings") if isinstance(assessment.get("confirmed_findings"), list) else []
    bundles = []
    for finding in findings:
        evidence = finding.get("evidence") if isinstance(finding.get("evidence"), dict) else {}
        items = [{"source": key, "value": value} for key, value in evidence.items()]
        bundles.append({
            "finding_code": finding.get("code"),
            "title": finding.get("title"),
            "severity": finding.get("severity"),
            "confidence": _confidence(len(items), True),
            "evidence": items,
            "evidence_hash": _hash(items),
            "decision": "confirmed" if items else "requires_additional_evidence",
            "challenge_policy": "Каждый вывод может быть оспорен только новым проверяемым evidence.",
        })
    return {
        "version": VERSION,
        "status": "ready" if bundles else "waiting_for_confirmed_findings",
        "bundles": bundles,
        "principles": ["traceable", "reproducible", "read_only", "unknown_is_not_missing"],
    }


def _data_quality_engine(pipeline: dict[str, Any]) -> dict[str, Any]:
    assessment = pipeline.get("best_practice_assessment") or {}
    validation = assessment.get("data_validation") if isinstance(assessment.get("data_validation"), dict) else {}
    required = validation.get("required_checks") if isinstance(validation.get("required_checks"), list) else []
    checks = [{"id": f"DQ-{idx:02d}", "title": title, "status": "planned", "read_only": True} for idx, title in enumerate(required, 1)]
    return {
        "version": VERSION,
        "status": "ready" if validation.get("status") == "confirmed" else "configuration_required",
        "score": None,
        "checks": checks,
        "metrics": {
            "matched_records": None,
            "missing_in_bitrix": None,
            "missing_in_onec": None,
            "duplicate_external_ids": None,
            "value_mismatches": None,
            "sync_delay_seconds": None,
        },
        "note": "Оценка качества данных появляется только после безопасных контрольных выборок из обеих систем.",
    }


def _drift_engine(pipeline: dict[str, Any]) -> dict[str, Any]:
    current = {
        "entity_mappings": pipeline.get("entity_mappings", []),
        "field_mappings": pipeline.get("field_mappings", []),
        "active_integration_artifacts": pipeline.get("active_integration_artifacts", []),
        "architecture_controls": (pipeline.get("best_practice_assessment") or {}).get("architecture_controls", []),
    }
    return {
        "version": VERSION,
        "status": "baseline_created",
        "snapshot_id": _hash(current)[:16],
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "fingerprint": _hash(current),
        "changes": [],
        "tracked_areas": list(current.keys()),
        "note": "Следующий аудит сравнивается с данным baseline; изменения не трактуются как дефект без оценки влияния.",
    }


def _business_impact_engine(pipeline: dict[str, Any]) -> dict[str, Any]:
    assessment = pipeline.get("best_practice_assessment") or {}
    findings = assessment.get("confirmed_findings") if isinstance(assessment.get("confirmed_findings"), list) else []
    severity_probability = {"critical": 0.9, "high": 0.75, "medium": 0.5, "low": 0.25}
    impacts = []
    for row in findings:
        severity = str(row.get("severity") or "medium")
        impacts.append({
            "code": row.get("code"),
            "title": row.get("title"),
            "severity": severity,
            "probability": severity_probability.get(severity, 0.5),
            "business_effect": row.get("impact"),
            "affected_capabilities": [row.get("area")],
            "priority": "immediate" if severity == "critical" else "high" if severity == "high" else "planned",
            "confidence": _confidence(len(row.get("evidence") or {}), True),
        })
    return {"version": VERSION, "status": "ready", "impacts": impacts}


def _copilot(pipeline: dict[str, Any]) -> dict[str, Any]:
    assessment = pipeline.get("best_practice_assessment") or {}
    recommendations = assessment.get("recommendations") if isinstance(assessment.get("recommendations"), list) else []
    playbooks = []
    for rec in recommendations:
        playbooks.append({
            "priority": rec.get("priority"),
            "title": rec.get("task"),
            "why": rec.get("basis"),
            "business_impact": rec.get("business_impact"),
            "implementation_mode": "proposal_only",
            "acceptance_test": rec.get("acceptance"),
            "anti_patterns": ["запись без внешнего ключа", "скрытая двусторонняя перезапись", "отсутствие повторяемого теста"],
            "questions_to_integrator": [
                "Какая система является источником истины?",
                "Как обеспечивается идемпотентность повторной отправки?",
                "Где фиксируются ошибки, ретраи и итоговый статус обмена?",
            ],
        })
    return {
        "version": VERSION,
        "status": "ready",
        "mode": "read_only_advisory",
        "playbooks": playbooks,
        "capabilities": ["design_review", "implementation_blueprint", "acceptance_criteria", "evidence_challenge"],
    }


def build_platform_v5(pipeline: dict[str, Any]) -> dict[str, Any]:
    evidence = _evidence_engine(pipeline)
    quality = _data_quality_engine(pipeline)
    drift = _drift_engine(pipeline)
    impact = _business_impact_engine(pipeline)
    copilot = _copilot(pipeline)
    return {
        "version": VERSION,
        "edition": "Unified Integration Intelligence Platform",
        "mode": "read_only",
        "status": "operational",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engines": {
            "evidence": evidence,
            "data_quality": quality,
            "drift_detection": drift,
            "business_impact": impact,
            "integrator_copilot": copilot,
        },
        "governance": {
            "write_to_bitrix": False,
            "write_to_onec": False,
            "unknown_is_not_missing": True,
            "confirmed_findings_only": True,
            "recommendations_are_proposals": True,
        },
        "readiness": {
            "evidence": evidence["status"],
            "data_quality": quality["status"],
            "drift_detection": drift["status"],
            "business_impact": impact["status"],
            "integrator_copilot": copilot["status"],
        },
    }
