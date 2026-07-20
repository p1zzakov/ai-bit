from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "3.4.2"


def _read(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _latest(root: Path, folder: str) -> dict[str, Any]:
    return _read(root / folder / "latest.json")


def _severity(value: Any) -> str:
    text = str(value or "medium").lower()
    if text in {"critical", "blocker"}:
        return "critical"
    if text in {"high", "error", "missing", "failed"}:
        return "high"
    if text in {"low", "info", "ok"}:
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


def _evidence(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items() if item not in (None, "")]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)]


def _add(
    rows: list[dict[str, Any]],
    *,
    module: str,
    title: str,
    finding: str,
    fix: str,
    evidence: Any = None,
    verification: str = "Повторно запустить аудит и убедиться, что отклонение больше не фиксируется.",
    severity: Any = "medium",
    source: str,
    confidence: Any = None,
) -> None:
    title = str(title or "").strip()
    finding = str(finding or "").strip()
    if not title and not finding:
        return
    rows.append(
        {
            "id": f"issue-{len(rows) + 1}",
            "module": str(module or "Общее").strip(),
            "severity": _severity(severity),
            "title": title or finding,
            "finding": finding or title,
            "evidence": _evidence(evidence),
            "fix": str(fix or "Проверить конфигурацию и привести её к методике внедрения.").strip(),
            "verification": str(verification or "Повторно запустить аудит.").strip(),
            "source": str(source or "unknown"),
            "confidence": _confidence(confidence),
        }
    )


def build_integrator_diagnostics(artifacts_dir: Path) -> dict[str, Any]:
    architecture = _latest(artifacts_dir, "business-architecture")
    operations = _latest(artifacts_dir, "operations")
    deep_rest = _latest(artifacts_dir, "deep-rest-evidence")
    evidence_audit = _latest(artifacts_dir, "evidence-audit")
    reference = _latest(artifacts_dir, "reference-audit")
    executive = _latest(artifacts_dir, "executive-intelligence")
    process_optimizer = executive.get("process_optimizer")
    if not isinstance(process_optimizer, dict):
        process_optimizer = {}

    issues: list[dict[str, Any]] = []

    for row in _rows(architecture.get("recommendations")):
        _add(
            issues,
            module=row.get("domain") or "Бизнес-архитектура",
            title=row.get("title") or "Архитектурное отклонение",
            finding=row.get("finding") or row.get("reason") or "",
            fix=row.get("action") or row.get("recommendation") or "",
            evidence=row.get("evidence"),
            severity=row.get("severity"),
            source="business_architecture",
            confidence=row.get("confidence"),
        )

    for row in _rows(operations.get("recommendations")):
        _add(
            issues,
            module=row.get("module") or "Задачи и управление",
            title=row.get("title") or "Операционное отклонение",
            finding=row.get("finding") or row.get("reason") or "",
            fix=row.get("action") or row.get("recommendation") or "",
            evidence=row.get("evidence"),
            severity=row.get("severity"),
            source="operations",
            confidence=row.get("confidence"),
        )

    for row in _rows(process_optimizer.get("top_recommendations")):
        confidence = _confidence(row.get("confidence"))
        _add(
            issues,
            module="Процессы",
            title=row.get("process") or row.get("title") or "Процесс требует доработки",
            finding=row.get("problem") or row.get("finding") or "",
            fix=row.get("recommendation") or row.get("action") or "",
            evidence=row.get("evidence"),
            severity="high" if (confidence or 0) >= 85 else "medium",
            source="process_optimizer",
            confidence=confidence,
        )

    for row in _rows(deep_rest.get("probes")):
        if row.get("success") is True or str(row.get("status") or "").lower() in {"ok", "success", "available"}:
            continue
        _add(
            issues,
            module=row.get("capability") or row.get("method") or "REST API",
            title="REST-проверка не пройдена",
            finding=row.get("error") or row.get("message") or "Метод недоступен или вернул ошибку.",
            fix="Проверить права вебхука, доступность REST-метода, редакцию Bitrix24 и настройки модуля.",
            evidence=[row.get("method"), row.get("http_status")],
            severity="high",
            source="deep_rest_evidence",
            verification="Повторить Deep REST Evidence и получить успешный ответ метода без ошибок доступа.",
        )

    gaps = reference.get("critical_gaps") or reference.get("gaps")
    for row in _rows(gaps):
        if str(row.get("status") or "").lower() not in {"missing", "partial", "failed"}:
            continue
        methodology = row.get("methodology") if isinstance(row.get("methodology"), dict) else {}
        audit = row.get("evidence_audit") if isinstance(row.get("evidence_audit"), dict) else {}
        _add(
            issues,
            module=row.get("domain") or row.get("category") or "Эталонная модель",
            title=row.get("title") or "Разрыв эталонной модели",
            finding=audit.get("rationale") or row.get("reason") or "Возможность не подтверждена фактическими данными.",
            fix=methodology.get("recommendation") or row.get("recommendation") or "Настроить возможность согласно методике и подтвердить её фактическим запуском.",
            evidence=row.get("evidence"),
            severity=row.get("status"),
            source="reference_audit",
            confidence=row.get("confidence"),
        )

    findings = evidence_audit.get("findings") or evidence_audit.get("issues")
    for row in _rows(findings):
        _add(
            issues,
            module=row.get("module") or row.get("capability") or "Evidence",
            title=row.get("title") or "Недостаточно доказательств",
            finding=row.get("finding") or row.get("rationale") or "",
            fix=row.get("recommendation") or row.get("action") or "Собрать недостающие доказательства и повторить аудит.",
            evidence=row.get("evidence"),
            severity=row.get("severity"),
            source="evidence_audit",
            confidence=row.get("confidence"),
        )

    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for item in issues:
        key = (item["module"].strip().lower(), item["title"].strip().lower())
        dedup.setdefault(key, item)
    issues = list(dedup.values())

    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda item: (rank.get(item["severity"], 9), -(item.get("confidence") or 0)))

    summary = {key: sum(1 for row in issues if row["severity"] == key) for key in ("critical", "high", "medium", "low")}
    summary["total"] = len(issues)
    summary["modules"] = len({row["module"] for row in issues})

    return {
        "version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "ok" if issues else "no_confirmed_issues",
        "summary": summary,
        "issues": issues,
        "sources": {
            "business_architecture": bool(architecture),
            "operations": bool(operations),
            "deep_rest_evidence": bool(deep_rest),
            "evidence_audit": bool(evidence_audit),
            "reference_audit": bool(reference),
            "executive_intelligence": bool(executive),
        },
        "principle": "Раздел содержит только технические отклонения, подтверждённые источниками AI-BIT. Отсутствие данных не трактуется как ошибка внедрения.",
    }
