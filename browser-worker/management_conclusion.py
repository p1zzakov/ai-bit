from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "2.0.0-alpha.7"
_DATE_KEYS = (
    "created", "date_create", "created_at", "start_date", "started_at",
    "date_start", "time_create", "created_date", "activity_date",
)
_EXCLUDED_KEYS = ("generated", "updated", "modified", "collected", "snapshot")
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+-Z]+)?$")


def _parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not _ISO_RE.match(text):
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    parsed = parsed.astimezone(UTC)
    now = datetime.now(UTC)
    if parsed.year < 2010 or parsed > now:
        return None
    return parsed


def _walk_dates(value: Any, path: str = "") -> list[tuple[datetime, str]]:
    found: list[tuple[datetime, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}" if path else str(key)
            if any(token in key_text for token in _EXCLUDED_KEYS):
                continue
            if any(token in key_text for token in _DATE_KEYS):
                parsed = _parse_date(child)
                if parsed:
                    found.append((parsed, child_path))
            found.extend(_walk_dates(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value[:5000]):
            found.extend(_walk_dates(child, f"{path}[{index}]"))
    return found


def _earliest_activity(artifacts_dir: Path) -> dict[str, Any]:
    candidates: list[tuple[datetime, str, str]] = []
    roots = [
        artifacts_dir / "operations" / "latest.json",
        artifacts_dir / "process-mining" / "latest.json",
        artifacts_dir / "business-architecture" / "latest.json",
    ]
    history = sorted((artifacts_dir / "history").glob("*.json"), reverse=True)[:20]
    for path in [*roots, *history]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for date_value, field_path in _walk_dates(payload):
            candidates.append((date_value, path.name, field_path))
    if not candidates:
        return {"first_activity_at": None, "age_days": None, "source": None, "confidence": "insufficient_data"}
    date_value, source, field_path = min(candidates, key=lambda row: row[0])
    age_days = max(0, (datetime.now(UTC) - date_value).days)
    return {
        "first_activity_at": date_value.isoformat(),
        "age_days": age_days,
        "source": f"{source}:{field_path}",
        "confidence": "system_evidence",
    }


def build_management_conclusion(result: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    source = result.get("source_summary") or {}
    maturity = result.get("digital_maturity") or {}
    reference = result.get("reference_audit") or {}
    ref_summary = reference.get("summary") or {}
    roi = result.get("roi") or {}
    timeline = _earliest_activity(artifacts_dir)

    overdue = float(source.get("overdue_rate") or 0)
    without_deadline = int(source.get("without_deadline") or 0)
    coverage = float(reference.get("coverage") or 0)
    missing = int(ref_summary.get("missing") or 0)
    partial = int(ref_summary.get("partial") or 0)
    score = float(maturity.get("score") or 0)

    findings: list[str] = []
    actions: list[str] = []
    consequences: list[str] = []

    if overdue >= 10:
        findings.append(f"{overdue:.1f}% открытых задач просрочено")
        actions.append("ужесточить еженедельный контроль просроченных задач и закрепить персональную ответственность руководителей подразделений")
        consequences.append("сроки исполнения поручений продолжат смещаться, а нагрузка будет накапливаться у ограниченного числа сотрудников")
    if without_deadline > 0:
        findings.append(f"{without_deadline} активных задач не имеют крайнего срока")
        actions.append("сделать срок обязательным для рабочих задач, шаблонов и автоматизированных процессов")
        consequences.append("часть поручений останется вне объективного контроля")
    if missing or partial:
        findings.append(f"покрытие эталонной модели составляет {coverage:.1f}%; не подтверждено {missing} возможностей, ещё {partial} реализованы частично")
        actions.append("утвердить поэтапный план завершения внедрения с владельцем, ответственным и сроком по каждому обязательному процессу")
        consequences.append("инвестиции в Bitrix24 будут использоваться частично, а ключевые операции останутся ручными или разрозненными")

    age_days = timeline.get("age_days")
    first_activity_at = timeline.get("first_activity_at")
    if age_days is not None and first_activity_at:
        first_date = datetime.fromisoformat(first_activity_at).strftime("%d.%m.%Y")
        findings.append(f"первые подтверждённые рабочие данные в доступных источниках относятся к {first_date}; наблюдаемый период составляет {age_days} дней")
        if age_days > 180 and coverage < 80:
            actions.append("зафиксировать дату завершения текущего этапа внедрения и прекратить работу без утверждённого календарного плана")
            consequences.append("при сохранении текущего темпа внедрение продолжит затягиваться")

    actions = list(dict.fromkeys(actions))[:5]
    consequences = list(dict.fromkeys(consequences))[:4]
    findings = list(dict.fromkeys(findings))[:6]

    if score >= 70 and coverage >= 75:
        status = "В целом система внедрена на рабочем уровне, однако отдельные организационные отклонения требуют управленческого контроля."
    elif score >= 55:
        status = "Система используется и приносит практическую пользу, но внедрение нельзя считать завершённым: результат ограничивают дисциплина исполнения и незакрытые цифровые процессы."
    else:
        status = "Текущее использование системы не обеспечивает достаточного уровня управляемости; требуется управленческое вмешательство и формализация программы внедрения."

    effect_parts: list[str] = []
    hours = float(roi.get("total_annual_hours") or 0)
    saving = roi.get("total_annual_saving_kzt")
    if hours > 0:
        effect_parts.append(f"до {hours:.0f} рабочих часов в год")
    if saving:
        effect_parts.append(f"ориентировочно {int(saving):,} ₸ в год".replace(",", " "))

    return {
        "version": VERSION,
        "status": status,
        "findings": findings,
        "required_actions": actions,
        "inaction_risks": consequences,
        "expected_effect": ", ".join(effect_parts) if effect_parts else "эффект требует дополнительного расчёта",
        "timeline": timeline,
        "summary": (
            "Исходя из выявленных данных, в первую очередь необходимо усилить контроль исполнения задач, "
            "исключить постановку поручений без сроков и перевести внедрение в формат управляемого проекта "
            "с утверждёнными этапами, сроками и ответственными."
        ),
    }
