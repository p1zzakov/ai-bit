from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ACTIVE_TASK_STATUSES = {"1", "2", "3", "4", "6"}
COMPLETED_TASK_STATUSES = {"5"}


def _now() -> datetime:
    return datetime.now(UTC)


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _rest_call_sync(webhook: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    base = webhook.rstrip("/") + "/"
    payload = urlencode(params or {}, doseq=True).encode("utf-8")
    request = Request(base + method + ".json", data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Bitrix REST HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:500]}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Bitrix REST connection failed: {exc}") from exc
    if data.get("error"):
        raise RuntimeError(f"Bitrix REST {data.get('error')}: {data.get('error_description', '')}")
    return data


async def rest_call(webhook: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await asyncio.to_thread(_rest_call_sync, webhook, method, params)


async def fetch_all(webhook: str, method: str, params: dict[str, Any] | None = None, limit: int = 5000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start = 0
    while len(rows) < limit:
        query = dict(params or {})
        query["start"] = start
        data = await rest_call(webhook, method, query)
        result = data.get("result", [])
        if isinstance(result, dict) and "tasks" in result:
            chunk = result.get("tasks") or []
        else:
            chunk = result if isinstance(result, list) else []
        rows.extend(item for item in chunk if isinstance(item, dict))
        next_value = data.get("next")
        if next_value is None or not chunk:
            break
        start = int(next_value)
    return rows[:limit]


def _user_name(user: dict[str, Any]) -> str:
    parts = [user.get("LAST_NAME"), user.get("NAME")]
    return " ".join(str(x).strip() for x in parts if x).strip() or str(user.get("EMAIL") or user.get("ID") or "Сотрудник")


def _department_ids(user: dict[str, Any]) -> list[str]:
    value = user.get("UF_DEPARTMENT") or []
    if not isinstance(value, list):
        value = [value]
    return [str(x) for x in value if x not in (None, "")]


def _task_metrics(task: dict[str, Any], now: datetime) -> dict[str, Any]:
    status = str(task.get("status") or task.get("STATUS") or "")
    deadline = _parse_dt(task.get("deadline") or task.get("DEADLINE"))
    closed = _parse_dt(task.get("closedDate") or task.get("CLOSED_DATE"))
    created = _parse_dt(task.get("createdDate") or task.get("CREATED_DATE"))
    active = status in ACTIVE_TASK_STATUSES or (status and status not in COMPLETED_TASK_STATUSES)
    completed = status in COMPLETED_TASK_STATUSES
    overdue = bool(active and deadline and deadline < now)
    no_deadline = bool(active and deadline is None)
    age_days = max(0, (now - created).days) if created else None
    duration_days = max(0, (closed - created).total_seconds() / 86400) if completed and created and closed else None
    return {
        "active": active,
        "completed": completed,
        "overdue": overdue,
        "no_deadline": no_deadline,
        "age_days": age_days,
        "duration_days": duration_days,
    }


def analyze_operational(users: list[dict[str, Any]], departments: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> dict[str, Any]:
    now = _now()
    user_map = {str(u.get("ID")): u for u in users if u.get("ID") is not None}
    department_map = {str(d.get("ID")): d for d in departments if d.get("ID") is not None}
    task_rows: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "open": 0, "overdue": 0, "without_deadline": 0, "completed": 0,
        "completion_days": [], "age_days": [], "created": 0,
    })

    totals = {"open": 0, "overdue": 0, "without_deadline": 0, "completed": 0}
    for task in tasks:
        responsible = str(task.get("responsibleId") or task.get("RESPONSIBLE_ID") or "0")
        creator = str(task.get("createdBy") or task.get("CREATED_BY") or "0")
        metrics = _task_metrics(task, now)
        row = task_rows[responsible]
        if metrics["active"]:
            row["open"] += 1; totals["open"] += 1
            if metrics["age_days"] is not None: row["age_days"].append(metrics["age_days"])
        if metrics["overdue"]:
            row["overdue"] += 1; totals["overdue"] += 1
        if metrics["no_deadline"]:
            row["without_deadline"] += 1; totals["without_deadline"] += 1
        if metrics["completed"]:
            row["completed"] += 1; totals["completed"] += 1
            if metrics["duration_days"] is not None: row["completion_days"].append(metrics["duration_days"])
        task_rows[creator]["created"] += 1

    employees: list[dict[str, Any]] = []
    for uid, user in user_map.items():
        row = task_rows[uid]
        open_count = row["open"]
        overdue_rate = round(row["overdue"] * 100 / open_count) if open_count else 0
        avg_completion = round(sum(row["completion_days"]) / len(row["completion_days"]), 1) if row["completion_days"] else None
        avg_age = round(sum(row["age_days"]) / len(row["age_days"]), 1) if row["age_days"] else None
        risk_points = min(100, overdue_rate + min(35, row["without_deadline"] * 2) + (20 if open_count > 50 else 10 if open_count > 30 else 0))
        dept_ids = _department_ids(user)
        employees.append({
            "id": uid,
            "name": _user_name(user),
            "email": user.get("EMAIL"),
            "active": str(user.get("ACTIVE", "Y")) == "Y",
            "department_ids": dept_ids,
            "departments": [str(department_map.get(d, {}).get("NAME") or d) for d in dept_ids],
            "open_tasks": open_count,
            "overdue_tasks": row["overdue"],
            "without_deadline": row["without_deadline"],
            "completed_tasks": row["completed"],
            "created_tasks": row["created"],
            "overdue_rate": overdue_rate,
            "avg_completion_days": avg_completion,
            "avg_open_age_days": avg_age,
            "risk_score": risk_points,
            "risk": "critical" if risk_points >= 70 else "high" if risk_points >= 45 else "medium" if risk_points >= 20 else "low",
        })

    department_rows: dict[str, dict[str, Any]] = defaultdict(lambda: {"employees": 0, "open": 0, "overdue": 0, "without_deadline": 0, "completed": 0})
    for employee in employees:
        for dept_id in employee["department_ids"] or ["unassigned"]:
            row = department_rows[dept_id]
            row["employees"] += 1
            row["open"] += employee["open_tasks"]
            row["overdue"] += employee["overdue_tasks"]
            row["without_deadline"] += employee["without_deadline"]
            row["completed"] += employee["completed_tasks"]

    department_analytics = []
    for dept_id, row in department_rows.items():
        rate = round(row["overdue"] * 100 / row["open"]) if row["open"] else 0
        department_analytics.append({
            "id": dept_id,
            "name": str(department_map.get(dept_id, {}).get("NAME") or "Без подразделения"),
            **row,
            "overdue_rate": rate,
            "risk": "critical" if rate >= 50 else "high" if rate >= 30 else "medium" if rate >= 15 else "low",
        })

    employees.sort(key=lambda x: (x["risk_score"], x["overdue_tasks"], x["open_tasks"]), reverse=True)
    department_analytics.sort(key=lambda x: (x["overdue_rate"], x["overdue"]), reverse=True)
    recommendations: list[dict[str, Any]] = []
    if totals["open"]:
        overdue_rate = round(totals["overdue"] * 100 / totals["open"])
        if overdue_rate >= 20:
            recommendations.append({"severity": "high", "title": "Системная просрочка задач", "finding": f"Просрочено {totals['overdue']} из {totals['open']} открытых задач ({overdue_rate}%).", "action": "Ввести еженедельный контроль просрочки, автоматическую эскалацию и владельцев SLA."})
    if totals["without_deadline"]:
        recommendations.append({"severity": "medium", "title": "Задачи без крайнего срока", "finding": f"Обнаружено {totals['without_deadline']} активных задач без deadline.", "action": "Сделать срок обязательным для рабочих шаблонов и типовых процессов."})
    overloaded = [x for x in employees if x["open_tasks"] > 40]
    if overloaded:
        recommendations.append({"severity": "high", "title": "Риск перегрузки сотрудников", "finding": f"У {len(overloaded)} сотрудников более 40 открытых задач.", "action": "Перераспределить очередь, выделить сервисные потоки и ограничить незавершённую работу."})

    return {
        "version": "0.9.0",
        "generated_at": now.isoformat(),
        "summary": {
            "users": len(users),
            "active_users": sum(1 for x in employees if x["active"]),
            "departments": len(departments),
            "tasks_loaded": len(tasks),
            **totals,
            "overdue_rate": round(totals["overdue"] * 100 / totals["open"]) if totals["open"] else 0,
            "employees_at_risk": sum(1 for x in employees if x["risk"] in {"critical", "high"}),
        },
        "employees": employees,
        "departments": department_analytics,
        "recommendations": recommendations,
        "methodology": "Индикаторы показывают дисциплину исполнения и нагрузку, но не являются оценкой ценности или качества работы сотрудника.",
    }


async def collect_operational_snapshot(artifacts_dir: Path) -> dict[str, Any]:
    webhook = os.getenv("BITRIX_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("BITRIX_WEBHOOK_URL is not configured")
    users, departments, tasks = await asyncio.gather(
        fetch_all(webhook, "user.get", {"filter[ACTIVE]": "Y"}, limit=5000),
        fetch_all(webhook, "department.get", {}, limit=5000),
        fetch_all(webhook, "tasks.task.list", {
            "select[]": ["ID", "TITLE", "STATUS", "RESPONSIBLE_ID", "CREATED_BY", "CREATED_DATE", "DEADLINE", "CLOSED_DATE"],
            "order[ID]": "asc",
        }, limit=20000),
    )
    result = analyze_operational(users, departments, tasks)
    root = artifacts_dir / "operations"
    root.mkdir(parents=True, exist_ok=True)
    stamp = _now().strftime("%Y%m%dT%H%M%SZ")
    path = root / f"operations-{stamp}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["artifact"] = str(path)
    return result


def read_latest_operational(artifacts_dir: Path) -> dict[str, Any]:
    path = artifacts_dir / "operations" / "latest.json"
    if not path.exists():
        raise FileNotFoundError("No operational snapshot")
    return json.loads(path.read_text(encoding="utf-8"))
