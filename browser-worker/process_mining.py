from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STOP_WORDS = {
    "и", "в", "во", "на", "по", "для", "к", "из", "от", "до", "с", "со", "о", "об",
    "за", "у", "под", "над", "при", "the", "a", "an", "to", "of", "for", "in", "on",
}


def _normalise_title(value: Any) -> str:
    text = str(value or "").lower().replace("ё", "е")
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\b\d+[\w./:-]*\b", " ", text)
    words = re.findall(r"[a-zа-я0-9]+", text)
    words = [word for word in words if word not in STOP_WORDS and len(word) > 2]
    return " ".join(words[:12])


def _name(user_map: dict[str, dict[str, Any]], user_id: str) -> str:
    return str(user_map.get(user_id, {}).get("name") or user_id or "Не определён")


def analyze_process_mining(operations: dict[str, Any]) -> dict[str, Any]:
    tasks = operations.get("task_events") or []
    employees = operations.get("employees") or []
    user_map = {str(item.get("id")): item for item in employees if item.get("id") is not None}

    title_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    handoffs: Counter[tuple[str, str]] = Counter()
    creator_patterns: Counter[str] = Counter()
    responsible_patterns: Counter[str] = Counter()

    for task in tasks:
        title_key = _normalise_title(task.get("title"))
        if title_key:
            title_groups[title_key].append(task)
        creator = str(task.get("creator_id") or "0")
        responsible = str(task.get("responsible_id") or "0")
        handoffs[(creator, responsible)] += 1
        creator_patterns[creator] += 1
        responsible_patterns[responsible] += 1

    repeated: list[dict[str, Any]] = []
    for key, rows in title_groups.items():
        if len(rows) < 3:
            continue
        open_count = sum(1 for row in rows if row.get("active"))
        overdue_count = sum(1 for row in rows if row.get("overdue"))
        no_deadline = sum(1 for row in rows if row.get("no_deadline"))
        creators = Counter(str(row.get("creator_id") or "0") for row in rows)
        responsibles = Counter(str(row.get("responsible_id") or "0") for row in rows)
        estimated_minutes = len(rows) * 5
        repeated.append({
            "pattern": key,
            "sample_title": rows[0].get("title") or key,
            "count": len(rows),
            "open": open_count,
            "overdue": overdue_count,
            "without_deadline": no_deadline,
            "top_creator": _name(user_map, creators.most_common(1)[0][0]),
            "top_responsible": _name(user_map, responsibles.most_common(1)[0][0]),
            "automation_score": min(100, 30 + len(rows) * 3 + overdue_count * 5 + no_deadline * 2),
            "estimated_manual_minutes": estimated_minutes,
            "recommendation": "Создать шаблон задачи или бизнес-процесс с автозаполнением ответственного, срока и контрольных шагов.",
        })
    repeated.sort(key=lambda item: (item["automation_score"], item["count"]), reverse=True)

    flows: list[dict[str, Any]] = []
    for (creator, responsible), count in handoffs.most_common(30):
        if count < 3 or creator == responsible:
            continue
        flows.append({
            "creator_id": creator,
            "creator": _name(user_map, creator),
            "responsible_id": responsible,
            "responsible": _name(user_map, responsible),
            "tasks": count,
            "recommendation": "Проверить типовой маршрут передачи и заменить повторяющуюся ручную постановку шаблоном, очередью или автоматическим назначением.",
        })

    bottlenecks: list[dict[str, Any]] = []
    for employee in employees:
        created = int(employee.get("created_tasks") or 0)
        open_tasks = int(employee.get("open_tasks") or 0)
        overdue = int(employee.get("overdue_tasks") or 0)
        if created >= 30 or open_tasks >= 40 or overdue >= 10:
            bottlenecks.append({
                "id": employee.get("id"),
                "name": employee.get("name"),
                "created_tasks": created,
                "open_tasks": open_tasks,
                "overdue_tasks": overdue,
                "risk": employee.get("risk"),
                "finding": "Высокая концентрация постановки или исполнения задач может указывать на ручной диспетчерский узел.",
                "recommendation": "Разделить поток по типам, назначить владельцев очередей и автоматизировать маршрутизацию.",
            })
    bottlenecks.sort(key=lambda item: (item["overdue_tasks"], item["open_tasks"], item["created_tasks"]), reverse=True)

    candidates = repeated[:20]
    total_minutes = sum(item["estimated_manual_minutes"] for item in candidates)
    return {
        "version": "1.0.0-beta.2",
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "tasks_analyzed": len(tasks),
            "repeated_patterns": len(repeated),
            "automation_candidates": len(candidates),
            "handoff_routes": len(flows),
            "potential_bottlenecks": len(bottlenecks),
            "estimated_manual_hours": round(total_minutes / 60, 1),
        },
        "automation_candidates": candidates,
        "handoff_routes": flows,
        "bottlenecks": bottlenecks[:25],
        "methodology": "MVP группирует похожие названия задач, повторяющиеся маршруты постановщик→исполнитель и концентрацию нагрузки. Оценка времени ориентировочная: 5 минут ручных действий на повторяющуюся задачу и требует подтверждения владельцем процесса.",
    }


def save_process_mining(artifacts_dir: Path, result: dict[str, Any]) -> Path:
    root = artifacts_dir / "process-mining"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "latest.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
