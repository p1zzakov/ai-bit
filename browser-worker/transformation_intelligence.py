from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

VERSION = "2.0.0-alpha.14"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _snapshot_points(artifacts_dir: Path, current: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = artifacts_dir / "executive-intelligence"
    for path in sorted(root.glob("*.json"))[-24:]:
        if path.name == "latest.json":
            continue
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append(item)
    rows.append(current)
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        stamp = str(row.get("generated_at") or "")
        if stamp:
            unique[stamp] = row
    return [unique[key] for key in sorted(unique)]


def build_roadmap(result: dict[str, Any]) -> dict[str, Any]:
    center = result.get("executive_kpi") or {}
    causes = center.get("root_causes") or []
    gaps = (result.get("reference_audit") or {}).get("critical_gaps") or []
    value = result.get("business_value") or {}
    total_effect = _num((value.get("total") or {}).get("annual_saving_kzt"))

    candidates: list[dict[str, Any]] = []
    for cause in causes:
        candidates.append({
            "title": cause.get("title") or "Устранение управленческого отклонения",
            "reason": cause.get("fact") or cause.get("root_cause") or "Выявлено системное отклонение.",
            "action": cause.get("recommended_action") or "Подготовить и утвердить корректирующий план.",
            "priority": int(_num(cause.get("priority"), 50)),
            "confidence": int(_num(cause.get("confidence"), 70)),
            "source": "root_cause",
        })
    for gap in gaps[:8]:
        if gap.get("status") not in {"missing", "partial"}:
            continue
        methodology = gap.get("methodology") or {}
        candidates.append({
            "title": gap.get("title") or "Цифровой разрыв",
            "reason": (gap.get("evidence_audit") or {}).get("rationale") or "Эталонная возможность не подтверждена полностью.",
            "action": methodology.get("recommendation") or "Назначить владельца процесса и определить критерии готовности.",
            "priority": 85 if gap.get("status") == "missing" else 70,
            "confidence": round(_num(gap.get("confidence")) * 100),
            "source": "reference_gap",
        })

    dedup: dict[str, dict[str, Any]] = {}
    for row in candidates:
        dedup.setdefault(str(row["title"]), row)
    ordered = sorted(dedup.values(), key=lambda x: (x["priority"], x["confidence"]), reverse=True)[:9]
    phases = [
        {"id": "phase_1", "title": "Стабилизация управления", "period": "1–2 недели", "items": []},
        {"id": "phase_2", "title": "Завершение ключевых процессов", "period": "3–6 недель", "items": []},
        {"id": "phase_3", "title": "Масштабирование и оптимизация", "period": "7–12 недель", "items": []},
    ]
    for index, item in enumerate(ordered):
        phase = 0 if item["priority"] >= 90 else 1 if item["priority"] >= 75 else 2
        item["owner_role"] = "Руководитель процесса совместно с ИТ"
        item["completion_criteria"] = "Назначен ответственный, установлен срок, результат подтверждён повторным аудитом AI-BIT."
        phases[phase]["items"].append(item)
    return {
        "version": "2.0.0-alpha.11",
        "phases": phases,
        "items_total": len(ordered),
        "annual_effect_reference_kzt": round(total_effect) if total_effect > 0 else None,
        "methodology": "Приоритет определяется по подтверждённым корневым причинам, критическим разрывам, уверенности доказательств и бизнес-влиянию.",
    }


def build_timeline(result: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    points = []
    for row in _snapshot_points(artifacts_dir, result):
        src = row.get("source_summary") or {}
        maturity = row.get("digital_maturity") or {}
        reference = row.get("reference_audit") or {}
        points.append({
            "generated_at": row.get("generated_at"),
            "maturity": _num(maturity.get("score")),
            "coverage": _num(reference.get("coverage")),
            "overdue_rate": _num(src.get("overdue_rate")),
            "without_deadline": int(_num(src.get("without_deadline"))),
        })
    first, last = (points[0], points[-1]) if points else ({}, {})
    return {
        "version": "2.0.0-alpha.12",
        "status": "ok" if len(points) >= 2 else "insufficient_history",
        "points": points[-12:],
        "available_snapshots": len(points),
        "deltas": {
            "maturity": round(_num(last.get("maturity")) - _num(first.get("maturity")), 1),
            "coverage": round(_num(last.get("coverage")) - _num(first.get("coverage")), 1),
            "overdue_rate": round(_num(last.get("overdue_rate")) - _num(first.get("overdue_rate")), 1),
            "without_deadline": int(_num(last.get("without_deadline")) - _num(first.get("without_deadline"))),
        } if len(points) >= 2 else {},
        "methodology": "История строится только по сохранённым снимкам Executive Intelligence.",
    }


def _linear_forecast(values: list[float], periods: int = 2) -> tuple[float, float]:
    if len(values) < 3:
        return values[-1] if values else 0.0, 0.0
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    trend = sum(changes[-4:]) / len(changes[-4:])
    return values[-1] + trend * periods, trend


def build_risk_forecast(timeline: dict[str, Any]) -> dict[str, Any]:
    points = timeline.get("points") or []
    if len(points) < 3:
        return {"version": "2.0.0-alpha.13", "status": "insufficient_history", "forecasts": [], "required_snapshots": 3, "available_snapshots": len(points)}
    metrics = {
        "overdue_rate": ("Просрочка задач", "%"),
        "without_deadline": ("Задачи без срока", ""),
        "maturity": ("Цифровая зрелость", " пунктов"),
        "coverage": ("Покрытие эталонной модели", "%"),
    }
    forecasts = []
    for key, (title, unit) in metrics.items():
        values = [_num(row.get(key)) for row in points]
        predicted, trend = _linear_forecast(values)
        predicted = max(0.0, min(100.0, predicted)) if key != "without_deadline" else max(0.0, predicted)
        worsening = trend > 0 if key in {"overdue_rate", "without_deadline"} else trend < 0
        forecasts.append({
            "metric": key,
            "title": title,
            "current": round(values[-1], 1),
            "forecast_two_periods": round(predicted, 1),
            "trend_per_snapshot": round(trend, 2),
            "direction": "worsening" if worsening else "improving" if trend else "stable",
            "unit": unit,
            "confidence": "medium" if len(points) < 6 else "high",
        })
    return {
        "version": "2.0.0-alpha.13",
        "status": "ok",
        "forecasts": forecasts,
        "available_snapshots": len(points),
        "warning": "Прогноз является линейной экстраполяцией фактической истории, а не гарантией будущего результата.",
    }


def build_ai_cio(result: dict[str, Any]) -> dict[str, Any]:
    roadmap = result.get("transformation_roadmap") or {}
    phases = roadmap.get("phases") or []
    value = result.get("business_value") or {}
    total = _num((value.get("total") or {}).get("annual_saving_kzt"))
    recommendations = []
    rank = 1
    for phase in phases:
        for item in phase.get("items") or []:
            recommendations.append({
                "rank": rank,
                "title": item.get("title"),
                "why": item.get("reason"),
                "decision": item.get("action"),
                "owner_role": item.get("owner_role"),
                "period": phase.get("period"),
                "confidence": item.get("confidence"),
                "expected_effect": "Входит в общий консервативный потенциал" if total > 0 else "Требует отдельного расчёта после назначения владельца процесса",
            })
            rank += 1
            if rank > 7:
                break
        if rank > 7:
            break
    return {
        "version": VERSION,
        "title": "Что бы сделал CIO в ближайшие 90 дней",
        "recommendations": recommendations,
        "annual_business_effect_reference_kzt": round(total) if total > 0 else None,
        "principle": "Рекомендации сформированы детерминированно по доказанным отклонениям. AI-провайдер не принимает управленческие решения.",
    }


def build_transformation_intelligence(result: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    roadmap = build_roadmap(result)
    timeline = build_timeline(result, artifacts_dir)
    forecast = build_risk_forecast(timeline)
    enriched = dict(result)
    enriched["transformation_roadmap"] = roadmap
    cio = build_ai_cio(enriched)
    return {"roadmap": roadmap, "timeline": timeline, "risk_forecast": forecast, "ai_cio": cio}
