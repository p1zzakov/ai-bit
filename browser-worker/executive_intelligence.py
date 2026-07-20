from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "1.0.0-rc.11"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _latest(artifacts_dir: Path, folder: str) -> dict[str, Any]:
    return _read_json(artifacts_dir / folder / "latest.json") or {}


def _latest_crawl(artifacts_dir: Path) -> dict[str, Any]:
    root = artifacts_dir / "history"
    for path in sorted(root.glob("*.json"), reverse=True):
        data = _read_json(path)
        if data:
            return data
    return {}


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return round(max(low, min(high, value)), 1)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def _level(score: float) -> str:
    if score >= 85:
        return "Высокий"
    if score >= 70:
        return "Выше среднего"
    if score >= 55:
        return "Средний"
    if score >= 40:
        return "Ниже среднего"
    return "Начальный"


def build_executive_intelligence(artifacts_dir: Path) -> dict[str, Any]:
    crawl = _latest_crawl(artifacts_dir)
    operations = _latest(artifacts_dir, "operations")
    architecture = _latest(artifacts_dir, "business-architecture")
    process_mining = _latest(artifacts_dir, "process-mining")

    assessment = crawl.get("assessment") or {}
    deep_audit = crawl.get("deep_audit") or {}
    op_summary = operations.get("summary") or {}
    arch_domains = architecture.get("domains") or {}
    pm_summary = process_mining.get("summary") or operations.get("process_mining_summary") or {}

    implementation = _num(assessment.get("implementation_score"), 50)
    enterprise_health = _num(architecture.get("enterprise_health"), 50)
    bp_score = _num((arch_domains.get("business_processes") or {}).get("score"), 50)
    crm_score = _num((arch_domains.get("crm") or {}).get("score"), 50)
    document_score = _num((arch_domains.get("documents") or {}).get("score"), 50)

    overdue_rate = _num(op_summary.get("overdue_rate"))
    without_deadline = _num(op_summary.get("without_deadline"))
    open_tasks = max(_num(op_summary.get("open")), 1)
    at_risk = _num(op_summary.get("employees_at_risk"))
    active_users = max(_num(op_summary.get("active_users") or op_summary.get("users")), 1)

    task_discipline = _clamp(100 - overdue_rate * 2.2 - (without_deadline / open_tasks * 100) * 0.55)
    management = _clamp(task_discipline * 0.65 + (100 - at_risk / active_users * 100) * 0.35)
    automation = _clamp(_num(pm_summary.get("automation_score"), 0) or min(85, 35 + _num(pm_summary.get("automation_candidates")) * 2.5))
    operations_score = _clamp(task_discipline * 0.7 + management * 0.3)

    dimensions = {
        "implementation": {"title": "Внедрение", "score": _clamp(implementation)},
        "management": {"title": "Управление", "score": management},
        "operations": {"title": "Исполнение задач", "score": operations_score},
        "processes": {"title": "Бизнес-процессы", "score": _clamp(bp_score)},
        "crm": {"title": "CRM и продажи", "score": _clamp(crm_score)},
        "documents": {"title": "Документооборот", "score": _clamp(document_score)},
        "automation": {"title": "Автоматизация", "score": automation},
    }
    maturity = _clamp(sum(item["score"] for item in dimensions.values()) / len(dimensions))
    for item in dimensions.values():
        item["grade"] = _grade(item["score"])

    risks: list[dict[str, Any]] = []
    if overdue_rate >= 20:
        risks.append({"severity": "critical", "title": "Высокая доля просроченных задач", "fact": f"Просрочено {overdue_rate:.1f}% открытых задач", "impact": "Снижение управляемости и задержки исполнения", "priority": 100})
    elif overdue_rate >= 10:
        risks.append({"severity": "high", "title": "Просрочка требует усиленного контроля", "fact": f"Просрочено {overdue_rate:.1f}% открытых задач", "impact": "Риски срыва сроков и перегрузки сотрудников", "priority": 85})
    if without_deadline > 0:
        risks.append({"severity": "high", "title": "Задачи создаются без срока", "fact": f"Без срока: {int(without_deadline)} задач", "impact": "Нельзя объективно контролировать исполнение", "priority": 90})
    if crm_score < 60:
        risks.append({"severity": "high", "title": "CRM используется недостаточно эффективно", "fact": f"Оценка CRM: {crm_score:.0f}/100", "impact": "Потеря прозрачности продаж и качества данных", "priority": 82})
    if document_score < 60:
        risks.append({"severity": "medium", "title": "Документооборот требует стандартизации", "fact": f"Оценка документооборота: {document_score:.0f}/100", "impact": "Задержки согласований и риск потери итоговых версий", "priority": 70})
    if automation < 55:
        risks.append({"severity": "medium", "title": "Низкий уровень автоматизации", "fact": f"Оценка автоматизации: {automation:.0f}/100", "impact": "Лишние ручные операции и потери рабочего времени", "priority": 75})
    risks.sort(key=lambda row: row["priority"], reverse=True)

    departments = operations.get("departments") or operations.get("department_stats") or []
    department_rating: list[dict[str, Any]] = []
    if isinstance(departments, dict):
        departments = [{"name": key, **(value if isinstance(value, dict) else {})} for key, value in departments.items()]
    for row in departments[:100]:
        name = str(row.get("name") or row.get("department") or row.get("title") or "Подразделение")
        rate = _num(row.get("overdue_rate"))
        no_deadline = _num(row.get("without_deadline"))
        open_count = max(_num(row.get("open")), 1)
        risk_count = _num(row.get("employees_at_risk"))
        score = _clamp(100 - rate * 1.8 - (no_deadline / open_count * 100) * 0.45 - risk_count * 3)
        department_rating.append({"name": name, "score": score, "grade": _grade(score), "overdue_rate": rate, "open": int(open_count)})
    department_rating.sort(key=lambda row: row["score"])

    candidates = process_mining.get("automation_candidates") or []
    hourly_cost = _num(os.getenv("ROI_HOURLY_COST_KZT"), 0)
    roi_items: list[dict[str, Any]] = []
    for row in candidates[:20]:
        hours = _num(row.get("estimated_manual_minutes")) / 60
        if hours <= 0:
            hours = _num(row.get("estimated_manual_hours"))
        annual_hours = round(hours * 12, 1)
        roi_items.append({
            "title": row.get("sample_title") or row.get("title") or "Кандидат на автоматизацию",
            "automation_score": _num(row.get("automation_score")),
            "annual_hours": annual_hours,
            "annual_saving_kzt": round(annual_hours * hourly_cost) if hourly_cost > 0 else None,
            "recommendation": row.get("recommendation") or "Проверить процесс и подготовить автоматизацию",
        })
    roi_items.sort(key=lambda row: (row["annual_saving_kzt"] or row["annual_hours"]), reverse=True)

    recommendations = []
    recommendations.extend(architecture.get("recommendations") or [])
    recommendations.extend(operations.get("recommendations") or [])
    recommendations.extend(deep_audit.get("action_plan") or [])
    roadmap = {"30_days": [], "60_days": [], "90_days": []}
    for row in recommendations:
        severity = str(row.get("severity", "")).lower()
        item = {"title": row.get("title") or row.get("action") or "Рекомендация", "action": row.get("action") or row.get("recommendation") or "", "severity": severity or "info"}
        if severity in {"critical", "high"} and len(roadmap["30_days"]) < 8:
            roadmap["30_days"].append(item)
        elif severity == "medium" and len(roadmap["60_days"]) < 8:
            roadmap["60_days"].append(item)
        elif len(roadmap["90_days"]) < 8:
            roadmap["90_days"].append(item)

    feed = []
    for risk in risks[:5]:
        feed.append({"type": "risk", "title": risk["title"], "text": risk["fact"], "severity": risk["severity"]})
    if department_rating:
        worst = department_rating[0]
        feed.append({"type": "department", "title": "Подразделение требует внимания", "text": f"{worst['name']}: рейтинг {worst['score']:.0f}/100", "severity": "high" if worst["score"] < 55 else "medium"})
    if roi_items:
        top = roi_items[0]
        feed.append({"type": "opportunity", "title": "Крупнейший кандидат на автоматизацию", "text": f"{top['title']} — до {top['annual_hours']:.0f} часов в год", "severity": "info"})

    result = {
        "version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "digital_maturity": {"score": maturity, "grade": _grade(maturity), "level": _level(maturity)},
        "dimensions": dimensions,
        "risks": risks,
        "department_rating": department_rating,
        "executive_feed": feed,
        "roi": {"hourly_cost_kzt": hourly_cost or None, "items": roi_items, "total_annual_hours": round(sum(item["annual_hours"] for item in roi_items), 1), "total_annual_saving_kzt": round(sum(item["annual_saving_kzt"] or 0 for item in roi_items)) if hourly_cost > 0 else None},
        "roadmap": roadmap,
        "source_summary": {"implementation_score": implementation, "enterprise_health": enterprise_health, "overdue_rate": overdue_rate, "without_deadline": int(without_deadline), "employees_at_risk": int(at_risk)},
    }
    root = artifacts_dir / "executive-intelligence"
    root.mkdir(parents=True, exist_ok=True)
    (root / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def read_latest_executive_intelligence(artifacts_dir: Path) -> dict[str, Any]:
    path = artifacts_dir / "executive-intelligence" / "latest.json"
    data = _read_json(path)
    if data is None:
        raise FileNotFoundError(path)
    return data
