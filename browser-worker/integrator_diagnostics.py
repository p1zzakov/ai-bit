from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "3.5.0"


def _read(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _latest(root: Path, folder: str) -> dict[str, Any]:
    return _read(root / folder / "latest.json")


def _rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        result: list[dict[str, Any]] = []
        for key, item in value.items():
            if isinstance(item, dict):
                row = dict(item)
                row.setdefault("title", str(key))
                result.append(row)
        return result
    return []


def _severity(value: Any) -> str:
    text = str(value or "medium").strip().lower()
    if text in {"critical", "blocker", "fatal"}:
        return "critical"
    if text in {"high", "error", "missing", "failed", "forbidden"}:
        return "high"
    if text in {"low", "info", "ok", "available", "success"}:
        return "low"
    return "medium"


def _confidence(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= number <= 1:
        number *= 100
    return round(max(0.0, min(100.0, number)), 1)


def _evidence(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items() if item not in (None, "", [], {})]
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            if item in (None, "", [], {}):
                continue
            if isinstance(item, dict):
                result.extend(_evidence(item))
            else:
                result.append(str(item))
        return result
    return [str(value)]


def _first(*values: Any, default: str = "") -> str:
    for value in values:
        if value not in (None, "", [], {}):
            return str(value).strip()
    return default


def _object_ref(row: dict[str, Any]) -> str:
    for key in (
        "object_ref", "entity", "entity_type", "method", "endpoint", "path",
        "process", "workflow", "field", "field_name", "id", "ID", "code",
    ):
        value = row.get(key)
        if value not in (None, ""):
            return f"{key}: {value}"
    return ""


def _add(
    issues: list[dict[str, Any]],
    *,
    module: str,
    title: str,
    finding: str,
    fix: str,
    source: str,
    severity: Any = "medium",
    evidence: Any = None,
    verification: str = "Повторить аудит и убедиться, что отклонение больше не фиксируется.",
    confidence: Any = None,
    object_ref: str = "",
    technical: dict[str, Any] | None = None,
) -> None:
    title = str(title or "").strip()
    finding = str(finding or "").strip()
    if not title and not finding:
        return
    issues.append(
        {
            "id": f"issue-{len(issues) + 1}",
            "module": str(module or "Общее").strip(),
            "severity": _severity(severity),
            "title": title or finding,
            "finding": finding or title,
            "object_ref": str(object_ref or "").strip(),
            "evidence": _evidence(evidence),
            "fix": str(fix or "Проверить конфигурацию объекта.").strip(),
            "verification": str(verification or "Повторить аудит.").strip(),
            "source": str(source or "unknown"),
            "confidence": _confidence(confidence),
            "technical": technical if isinstance(technical, dict) else {},
        }
    )


def build_integrator_diagnostics(artifacts_dir: Path) -> dict[str, Any]:
    architecture = _latest(artifacts_dir, "business-architecture")
    operations = _latest(artifacts_dir, "operations")
    deep_rest = _latest(artifacts_dir, "deep-rest-evidence")
    evidence_audit = _latest(artifacts_dir, "evidence-audit")
    reference = _latest(artifacts_dir, "reference-audit")
    executive = _latest(artifacts_dir, "executive-intelligence")
    capability = _latest(artifacts_dir, "capability-discovery")

    process_optimizer = executive.get("process_optimizer")
    if not isinstance(process_optimizer, dict):
        process_optimizer = {}

    issues: list[dict[str, Any]] = []

    for row in _rows(architecture.get("recommendations")):
        _add(
            issues,
            module=_first(row.get("domain"), row.get("module"), default="Бизнес-архитектура"),
            title=_first(row.get("title"), default="Архитектурное отклонение"),
            finding=_first(row.get("finding"), row.get("reason"), row.get("description")),
            fix=_first(row.get("action"), row.get("recommendation"), row.get("fix")),
            evidence=row.get("evidence"),
            severity=row.get("severity"),
            source="business_architecture",
            confidence=row.get("confidence"),
            object_ref=_object_ref(row),
            technical=row,
        )

    for row in _rows(operations.get("recommendations")):
        _add(
            issues,
            module=_first(row.get("module"), row.get("department"), default="Задачи и управление"),
            title=_first(row.get("title"), default="Операционное отклонение"),
            finding=_first(row.get("finding"), row.get("reason"), row.get("description")),
            fix=_first(row.get("action"), row.get("recommendation"), row.get("fix")),
            evidence=row.get("evidence"),
            severity=row.get("severity"),
            source="operations",
            confidence=row.get("confidence"),
            object_ref=_object_ref(row),
            technical=row,
        )

    for row in _rows(process_optimizer.get("top_recommendations")):
        confidence = _confidence(row.get("confidence"))
        _add(
            issues,
            module="Процессы",
            title=_first(row.get("process"), row.get("title"), default="Процесс требует доработки"),
            finding=_first(row.get("problem"), row.get("finding"), row.get("reason")),
            fix=_first(row.get("recommendation"), row.get("action"), row.get("fix")),
            evidence=row.get("evidence"),
            severity="high" if (confidence or 0) >= 85 else "medium",
            source="process_optimizer",
            confidence=confidence,
            object_ref=_object_ref(row),
            technical=row,
        )

    rest_checks: list[dict[str, Any]] = []
    for row in _rows(deep_rest.get("probes")):
        status_text = str(row.get("status") or "").lower()
        success = row.get("success") is True or status_text in {"ok", "success", "available"}
        rest_item = {
            "method": _first(row.get("method"), row.get("endpoint"), row.get("capability"), default="unknown"),
            "capability": _first(row.get("capability"), row.get("module")),
            "status": "ok" if success else "error",
            "http_status": row.get("http_status") or row.get("status_code"),
            "error": _first(row.get("error"), row.get("message")),
            "duration_ms": row.get("duration_ms") or row.get("elapsed_ms"),
            "evidence": _evidence(row.get("evidence")),
        }
        rest_checks.append(rest_item)
        if success:
            continue
        _add(
            issues,
            module=_first(row.get("capability"), row.get("module"), default="REST API"),
            title="REST-проверка не пройдена",
            finding=_first(row.get("error"), row.get("message"), default="Метод недоступен или вернул ошибку."),
            fix="Проверить права вебхука, доступность REST-метода, редакцию Bitrix24 и параметры запроса.",
            evidence=[row.get("method"), row.get("http_status"), row.get("evidence")],
            severity="high",
            source="deep_rest_evidence",
            verification="Повторить REST-проверку и получить успешный ответ метода.",
            object_ref=_first(row.get("method"), row.get("endpoint")),
            technical=row,
        )

    gaps = reference.get("critical_gaps") or reference.get("gaps")
    reference_diff: list[dict[str, Any]] = []
    for row in _rows(gaps):
        status = str(row.get("status") or "unknown").lower()
        reference_diff.append(
            {
                "module": _first(row.get("domain"), row.get("category"), default="Эталонная модель"),
                "capability": _first(row.get("title"), row.get("capability"), row.get("id"), default="Неизвестная возможность"),
                "status": status,
                "evidence": _evidence(row.get("evidence")),
                "object_ref": _object_ref(row),
            }
        )
        if status not in {"missing", "partial", "failed"}:
            continue
        methodology = row.get("methodology") if isinstance(row.get("methodology"), dict) else {}
        audit = row.get("evidence_audit") if isinstance(row.get("evidence_audit"), dict) else {}
        _add(
            issues,
            module=_first(row.get("domain"), row.get("category"), default="Эталонная модель"),
            title=_first(row.get("title"), default="Разрыв эталонной модели"),
            finding=_first(audit.get("rationale"), row.get("reason"), default="Возможность не подтверждена фактическими данными."),
            fix=_first(methodology.get("recommendation"), row.get("recommendation"), default="Настроить возможность по методике и подтвердить фактическим запуском."),
            evidence=row.get("evidence"),
            severity=status,
            source="reference_audit",
            confidence=row.get("confidence"),
            object_ref=_object_ref(row),
            technical=row,
        )

    findings = evidence_audit.get("findings") or evidence_audit.get("issues")
    for row in _rows(findings):
        _add(
            issues,
            module=_first(row.get("module"), row.get("capability"), default="Evidence"),
            title=_first(row.get("title"), default="Недостаточно доказательств"),
            finding=_first(row.get("finding"), row.get("rationale"), row.get("reason")),
            fix=_first(row.get("recommendation"), row.get("action"), default="Собрать недостающие доказательства и повторить аудит."),
            evidence=row.get("evidence"),
            severity=row.get("severity"),
            source="evidence_audit",
            confidence=row.get("confidence"),
            object_ref=_object_ref(row),
            technical=row,
        )

    dedup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in issues:
        key = (
            item["module"].strip().lower(),
            item["title"].strip().lower(),
            item.get("object_ref", "").strip().lower(),
        )
        dedup.setdefault(key, item)
    issues = list(dedup.values())

    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda item: (rank.get(item["severity"], 9), item["module"], item["title"]))

    summary = {key: sum(1 for row in issues if row["severity"] == key) for key in ("critical", "high", "medium", "low")}
    summary["total"] = len(issues)
    summary["modules"] = len({row["module"] for row in issues})

    module_summary: list[dict[str, Any]] = []
    for module in sorted({row["module"] for row in issues}):
        rows = [row for row in issues if row["module"] == module]
        module_summary.append(
            {
                "module": module,
                "total": len(rows),
                "critical": sum(1 for row in rows if row["severity"] == "critical"),
                "high": sum(1 for row in rows if row["severity"] == "high"),
                "medium": sum(1 for row in rows if row["severity"] == "medium"),
                "low": sum(1 for row in rows if row["severity"] == "low"),
            }
        )

    technical_todo = [
        {
            "priority": index + 1,
            "module": row["module"],
            "object_ref": row.get("object_ref", ""),
            "task": row["fix"],
            "acceptance": row["verification"],
            "source": row["source"],
            "severity": row["severity"],
        }
        for index, row in enumerate(issues)
        if row["severity"] in {"critical", "high", "medium"}
    ]

    sources = {
        "business_architecture": bool(architecture),
        "operations": bool(operations),
        "deep_rest_evidence": bool(deep_rest),
        "evidence_audit": bool(evidence_audit),
        "reference_audit": bool(reference),
        "executive_intelligence": bool(executive),
        "capability_discovery": bool(capability),
    }

    inventory = {
        "generated_at": datetime.now(UTC).isoformat(),
        "available_sources": sum(1 for value in sources.values() if value),
        "total_sources": len(sources),
        "rest_probes": len(rest_checks),
        "rest_failed": sum(1 for row in rest_checks if row["status"] != "ok"),
        "reference_checks": len(reference_diff),
        "confirmed_issues": len(issues),
    }

    return {
        "version": VERSION,
        "generated_at": inventory["generated_at"],
        "status": "ok" if issues else "no_confirmed_issues",
        "inventory": inventory,
        "summary": summary,
        "module_summary": module_summary,
        "issues": issues,
        "rest_checks": rest_checks,
        "reference_diff": reference_diff,
        "technical_todo": technical_todo,
        "sources": sources,
        "principle": "Только подтверждённые технические факты. Нет evidence — нет замечания.",
    }
