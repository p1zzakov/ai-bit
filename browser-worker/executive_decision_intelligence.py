from __future__ import annotations

from typing import Any

VERSION = "3.3.0"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "E"


def build_executive_score(result: dict[str, Any]) -> dict[str, Any]:
    dimensions = result.get("dimensions") or {}
    weighted = {
        "implementation": 0.15,
        "management": 0.20,
        "operations": 0.20,
        "processes": 0.15,
        "crm": 0.10,
        "documents": 0.10,
        "automation": 0.10,
    }
    components = []
    total = 0.0
    used_weight = 0.0
    for key, weight in weighted.items():
        row = dimensions.get(key)
        if not isinstance(row, dict) or row.get("score") is None:
            continue
        score = _clamp(_num(row.get("score")))
        contribution = score * weight
        total += contribution
        used_weight += weight
        components.append({
            "id": key,
            "title": row.get("title") or key,
            "score": score,
            "weight": round(weight * 100),
            "contribution": round(contribution, 1),
        })
    score = _clamp(total / used_weight) if used_weight else 0.0
    target = 80.0
    return {
        "version": VERSION,
        "score": score,
        "grade": _grade(score),
        "target": target,
        "gap_to_target": round(max(0.0, target - score), 1),
        "status": "target_reached" if score >= target else "improvement_required",
        "components": components,
        "coverage_percent": round(used_weight * 100),
        "methodology": "Взвешенный индекс подтверждённых контуров: управление и исполнение по 20%; внедрение и процессы по 15%; CRM, документооборот и автоматизация по 10%.",
    }


def build_department_maturity(result: dict[str, Any]) -> dict[str, Any]:
    rows = result.get("department_rating") or []
    departments = []
    for row in rows:
        score = _clamp(_num(row.get("score")))
        departments.append({
            "name": row.get("name") or "Подразделение",
            "score": score,
            "grade": _grade(score),
            "overdue_rate": round(_num(row.get("overdue_rate")), 1),
            "open_tasks": int(_num(row.get("open"))),
            "evidence_scope": "Исполнительская дисциплина по задачам Bitrix24",
        })
    departments.sort(key=lambda item: item["score"])
    return {
        "version": VERSION,
        "status": "ok" if departments else "insufficient_data",
        "departments": departments,
        "lowest": departments[:5],
        "highest": list(reversed(departments[-5:])),
        "methodology": "Оценка отражает только подтверждённую дисциплину задач: просрочку, задачи без срока и концентрацию риска. Она не является оценкой ценности или общей эффективности подразделения.",
    }


def build_ai_timeline(result: dict[str, Any]) -> dict[str, Any]:
    timeline = result.get("executive_timeline") or {}
    points = timeline.get("points") or []
    deltas = timeline.get("deltas") or {}
    highlights = []
    labels = {
        "maturity": ("Цифровая зрелость", True, " п."),
        "coverage": ("Покрытие эталонной модели", True, " п.п."),
        "overdue_rate": ("Просрочка", False, " п.п."),
        "without_deadline": ("Задачи без срока", False, ""),
    }
    for key, (title, positive_growth, suffix) in labels.items():
        if key not in deltas:
            continue
        delta = round(_num(deltas.get(key)), 1)
        improved = delta > 0 if positive_growth else delta < 0
        direction = "improved" if improved else "worsened" if delta else "stable"
        highlights.append({
            "metric": key,
            "title": title,
            "delta": delta,
            "suffix": suffix,
            "direction": direction,
        })
    return {
        "version": VERSION,
        "status": "ok" if len(points) >= 2 else "insufficient_history",
        "available_snapshots": len(points),
        "points": points,
        "highlights": highlights,
        "period_start": points[0].get("generated_at") if points else None,
        "period_end": points[-1].get("generated_at") if points else None,
        "methodology": "Динамика рассчитывается только по сохранённым снимкам Executive Intelligence. Прогнозные и финансовые допущения не используются.",
    }


def build_evidence_ai_cio(result: dict[str, Any]) -> dict[str, Any]:
    existing = (result.get("ai_cio") or {}).get("recommendations") or []
    risks = result.get("risks") or []
    recommendations = []
    seen: set[str] = set()

    for item in existing:
        title = str(item.get("title") or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        recommendations.append({
            "rank": len(recommendations) + 1,
            "title": title,
            "why": item.get("why") or "Подтверждено данными аудита.",
            "decision": item.get("decision") or "Назначить владельца и утвердить корректирующее действие.",
            "owner_role": item.get("owner_role") or "Владелец процесса совместно с ИТ",
            "period": item.get("period") or "До 30 дней",
            "confidence": int(_num(item.get("confidence"), 70)),
            "evidence_type": "roadmap_and_root_cause",
        })
        if len(recommendations) >= 7:
            break

    for risk in risks:
        if len(recommendations) >= 7:
            break
        title = str(risk.get("title") or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        recommendations.append({
            "rank": len(recommendations) + 1,
            "title": title,
            "why": risk.get("fact") or "Подтверждено фактическим отклонением.",
            "decision": "Утвердить владельца, срок исправления и проверить результат повторным аудитом.",
            "owner_role": "Руководитель соответствующего процесса",
            "period": "До 30 дней" if risk.get("severity") in {"critical", "high"} else "До 90 дней",
            "confidence": 85,
            "evidence_type": "confirmed_risk",
        })

    return {
        "version": VERSION,
        "title": "Рекомендации AI CIO",
        "recommendations": recommendations,
        "principle": "Решения сформированы детерминированно по подтверждённым отклонениям. Финансовые оценки и неподтверждённые предположения исключены.",
    }


def enrich_executive_decision_intelligence(result: dict[str, Any]) -> dict[str, Any]:
    result["executive_score"] = build_executive_score(result)
    result["department_maturity"] = build_department_maturity(result)
    result["ai_timeline"] = build_ai_timeline(result)
    result["ai_cio"] = build_evidence_ai_cio(result)
    return result
