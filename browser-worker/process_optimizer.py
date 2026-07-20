from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

VERSION = "2.0.0-alpha.15"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(value: Any) -> str:
    return str(value or "").strip()


def _latest_json(directory: Path) -> dict[str, Any]:
    if not directory.exists():
        return {}
    files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, ValueError, TypeError):
            continue
    return {}


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _first_number(item: dict[str, Any], keys: tuple[str, ...]) -> float:
    lowered = {str(k).lower(): v for k, v in item.items()}
    for key in keys:
        if key.lower() in lowered:
            return _num(lowered[key.lower()])
    return 0.0


def _first_text(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    lowered = {str(k).lower(): v for k, v in item.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()] not in (None, ""):
            return _text(lowered[key.lower()])
    return ""


def _normalise_process_mining(source: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for index, item in enumerate(source.get("automation_candidates") or [], 1):
        if not isinstance(item, dict):
            continue
        name = _text(item.get("sample_title") or item.get("pattern"))
        if not name:
            continue
        count = int(_num(item.get("count")))
        overdue = int(_num(item.get("overdue")))
        without_deadline = int(_num(item.get("without_deadline")))
        result.append({
            "id": f"pattern-{index}",
            "name": name,
            "source_type": "automation_candidate",
            "runs": count,
            "open": int(_num(item.get("open"))),
            "overdue": overdue,
            "without_deadline": without_deadline,
            "automation_score": _num(item.get("automation_score")),
            "estimated_manual_minutes": _num(item.get("estimated_manual_minutes")),
            "top_creator": _text(item.get("top_creator")),
            "top_responsible": _text(item.get("top_responsible")),
            "participants": 1 if item.get("top_responsible") else 0,
            "manual_actions": 1,
            "robots": 0,
            "triggers": 0,
            "sla": count > 0 and without_deadline == 0,
            "source_recommendation": _text(item.get("recommendation")),
        })

    for index, item in enumerate(source.get("handoff_routes") or [], 1):
        if not isinstance(item, dict):
            continue
        creator = _text(item.get("creator"))
        responsible = _text(item.get("responsible"))
        tasks = int(_num(item.get("tasks")))
        if not creator or not responsible or tasks <= 0:
            continue
        result.append({
            "id": f"route-{index}",
            "name": f"Маршрут: {creator} → {responsible}",
            "source_type": "handoff_route",
            "runs": tasks,
            "participants": 2,
            "manual_actions": 1,
            "robots": 0,
            "triggers": 0,
            "route_creator": creator,
            "route_responsible": responsible,
            "source_recommendation": _text(item.get("recommendation")),
        })

    return result


def _collect_generic_processes(*sources: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    name_keys = (
        "name", "title", "process", "process_name", "workflow", "template_name",
        "sample_title", "pattern",
    )
    signal_keys = {
        "stages", "steps", "stage_count", "step_count", "duration", "duration_hours",
        "average_duration", "avg_duration", "executions", "runs", "instances", "count",
        "automation", "automation_score", "robots", "triggers", "sla", "participants", "owners",
        "without_deadline", "overdue", "tasks",
    }
    for source in sources:
        for node in _walk(source):
            if not isinstance(node, dict):
                continue
            lowered_keys = {str(k).lower() for k in node}
            if not lowered_keys.intersection(signal_keys):
                continue
            name = _first_text(node, name_keys)
            if name:
                candidates.append(node)
    return candidates


def _collect_processes(process_mining: dict[str, Any], *sources: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = _normalise_process_mining(process_mining)
    candidates.extend(_collect_generic_processes(*sources))
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        name = _first_text(item, ("name", "title", "process", "process_name", "workflow", "template_name", "sample_title", "pattern"))
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _recommendation(process_id: str, process_name: str, problem: str, recommendation: str,
                    effect: str, confidence: int, category: str, priority: int,
                    evidence: list[str]) -> dict[str, Any]:
    return {
        "id": f"{process_id}:{category}",
        "process_id": process_id,
        "process": process_name,
        "category": category,
        "problem": problem,
        "recommendation": recommendation,
        "expected_effect": effect,
        "confidence": confidence,
        "priority": priority,
        "evidence": evidence,
        "project_generator_payload": {
            "title": f"Оптимизация процесса: {process_name}",
            "problem": problem,
            "target_result": recommendation,
            "expected_effect": effect,
            "source": "AI Process Optimizer",
        },
    }


def _analyse_process(item: dict[str, Any], index: int) -> dict[str, Any]:
    name = _first_text(item, ("name", "title", "process", "process_name", "workflow", "template_name", "sample_title", "pattern")) or f"Процесс {index}"
    process_id = _first_text(item, ("id", "process_id", "template_id", "workflow_id")) or f"process-{index}"
    stages = _first_number(item, ("stage_count", "step_count", "stages_count", "steps_count", "stages", "steps"))
    avg_hours = _first_number(item, ("average_duration_hours", "avg_duration_hours", "duration_hours", "average_duration", "avg_duration"))
    runs = _first_number(item, ("executions", "runs", "instances", "items", "count", "tasks"))
    robots = _first_number(item, ("robots", "robot_count", "automation_rules"))
    triggers = _first_number(item, ("triggers", "trigger_count"))
    manual = _first_number(item, ("manual_actions", "manual_steps", "human_tasks"))
    loops = _first_number(item, ("loops", "cycles", "returns", "backward_transitions"))
    errors = _first_number(item, ("errors", "failed", "failed_runs", "error_count"))
    participants = _first_number(item, ("participants", "participant_count", "owners", "assignees"))
    overdue = _first_number(item, ("overdue", "overdue_tasks"))
    without_deadline = _first_number(item, ("without_deadline", "no_deadline"))
    open_items = _first_number(item, ("open", "open_tasks"))
    manual_minutes = _first_number(item, ("estimated_manual_minutes",))
    sla = bool(item.get("sla") or item.get("deadline") or item.get("time_limit") or item.get("target_duration"))

    score = 100.0
    recommendations: list[dict[str, Any]] = []
    evidence: list[str] = []

    if stages:
        evidence.append(f"Обнаружено этапов: {int(stages)}")
    if avg_hours:
        evidence.append(f"Средняя длительность: {avg_hours:.1f} ч")
    if runs:
        evidence.append(f"Подтверждённых повторений/запусков: {int(runs)}")
    if overdue:
        evidence.append(f"Просрочено: {int(overdue)}")
    if without_deadline:
        evidence.append(f"Без срока: {int(without_deadline)}")
    if manual_minutes:
        evidence.append(f"Оценка ручных затрат: {int(manual_minutes)} мин")

    if stages > 9:
        score -= min(24, (stages - 9) * 3)
        recommendations.append(_recommendation(
            process_id, name, f"Маршрут содержит {int(stages)} этапов.",
            "Объединить дублирующие проверки и оставить только контрольные точки, влияющие на решение.",
            "Сокращение времени прохождения и числа передач.", 88, "excessive_steps", 86,
            [f"Количество этапов: {int(stages)}"],
        ))

    if loops > 0:
        score -= min(22, loops * 6)
        recommendations.append(_recommendation(
            process_id, name, f"Обнаружены возвраты или циклические переходы: {int(loops)}.",
            "Разделить возврат на исправление и повторное согласование и исключить повторное прохождение подтверждённых этапов.",
            "Снижение повторной работы.", 93, "loops", 96,
            [f"Циклические переходы: {int(loops)}"],
        ))

    if runs >= 3 and robots + triggers == 0:
        score -= 16
        source_rec = _text(item.get("source_recommendation"))
        recommendations.append(_recommendation(
            process_id, name, "Повторяющийся рабочий поток выполняется без подтверждённой автоматизации.",
            source_rec or "Создать шаблон, робота или бизнес-процесс с автозаполнением ответственного, срока и контрольных шагов.",
            "Сокращение ручных операций и зависимости от дисциплины участников.", 90, "low_automation", 92,
            [f"Повторений: {int(runs)}", "Роботы и триггеры не подтверждены"],
        ))

    if without_deadline > 0:
        share = without_deadline / max(1.0, runs) * 100
        score -= min(22, 8 + share * 0.18)
        recommendations.append(_recommendation(
            process_id, name, f"Без срока остаётся {int(without_deadline)} из {int(runs)} повторений ({share:.1f}%).",
            "Закрепить срок в шаблоне процесса и автоматически рассчитывать его от даты запуска.",
            "Повышение управляемости исполнения и снижение скрытой просрочки.", 96, "missing_deadlines", 98,
            [f"Без срока: {int(without_deadline)}", f"Всего повторений: {int(runs)}"],
        ))

    if overdue > 0:
        base = open_items if open_items > 0 else runs
        rate = overdue / max(1.0, base) * 100
        score -= min(22, 7 + rate * 0.25)
        recommendations.append(_recommendation(
            process_id, name, f"Обнаружено {int(overdue)} просроченных элементов ({rate:.1f}% от активного объёма).",
            "Добавить предупредительную эскалацию, владельца SLA и регулярный контроль незавершённых элементов.",
            "Снижение просрочки и накопления незавершённой работы.", 95, "overdue_flow", 97,
            [f"Просрочено: {int(overdue)}", f"Активный объём: {int(base)}"],
        ))

    if manual >= 4:
        score -= min(18, manual * 2)
        recommendations.append(_recommendation(
            process_id, name, f"Подтверждено ручных действий: {int(manual)}.",
            "Механические операции перенести в роботов, правила и автозаполнение.",
            "Снижение трудозатрат и ошибок ввода.", 86, "manual_work", 84,
            [f"Ручные действия: {int(manual)}"],
        ))

    if avg_hours >= 72 and not sla:
        score -= 15
        recommendations.append(_recommendation(
            process_id, name, f"Средняя длительность составляет {avg_hours / 24:.1f} дня, SLA не подтверждён.",
            "Установить SLA процесса и этапов, предупреждение и эскалацию владельцу процесса.",
            "Повышение прогнозируемости сроков.", 89, "missing_sla", 90,
            [f"Средняя длительность: {avg_hours:.1f} ч", "SLA не подтверждён"],
        ))

    if errors > 0:
        score -= min(20, errors * 3)
        recommendations.append(_recommendation(
            process_id, name, f"Обнаружены ошибки выполнения: {int(errors)}.",
            "Добавить валидацию данных и контроль отказавших роботов.",
            "Снижение числа остановленных экземпляров.", 94, "execution_errors", 98,
            [f"Ошибки выполнения: {int(errors)}"],
        ))

    if participants == 1 and runs >= 3:
        score -= 12
        recommendations.append(_recommendation(
            process_id, name, "Поток связан с одним подтверждённым исполнителем.",
            "Назначить роль или группу вместо конкретного сотрудника и определить замещение.",
            "Снижение зависимости от одного сотрудника.", 84, "single_point_dependency", 83,
            ["Один подтверждённый исполнитель", f"Повторений: {int(runs)}"],
        ))

    if runs == 0:
        score = min(score, 55)
        recommendations.append(_recommendation(
            process_id, name, "Фактические запуски процесса не подтверждены.",
            "Проверить ввод процесса в эксплуатацию и доступность пользователям.",
            "Исключение формально настроенных, но неиспользуемых процессов.", 72, "unused_process", 70,
            ["Запуски не подтверждены"],
        ))

    score = round(max(0.0, min(100.0, score)), 1)
    status = "optimized" if score >= 80 else "improvable" if score >= 60 else "redesign"
    recommendations.sort(key=lambda x: x["priority"], reverse=True)

    return {
        "id": process_id,
        "name": name,
        "source_type": _text(item.get("source_type")) or "system_entity",
        "score": score,
        "status": status,
        "metrics": {
            "stages": int(stages),
            "average_duration_hours": round(avg_hours, 1),
            "runs": int(runs),
            "robots": int(robots),
            "triggers": int(triggers),
            "manual_actions": int(manual),
            "loops": int(loops),
            "errors": int(errors),
            "participants": int(participants),
            "open": int(open_items),
            "overdue": int(overdue),
            "without_deadline": int(without_deadline),
            "estimated_manual_minutes": int(manual_minutes),
            "sla_detected": sla,
        },
        "evidence": evidence,
        "recommendations": recommendations,
    }


def build_process_optimizer(result: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    process_mining = _latest_json(artifacts_dir / "process-mining")
    architecture = _latest_json(artifacts_dir / "business-architecture")
    deep_rest = _latest_json(artifacts_dir / "deep-rest-evidence")
    processes = _collect_processes(process_mining, architecture, deep_rest)
    analysed = [_analyse_process(item, index + 1) for index, item in enumerate(processes)]
    analysed.sort(key=lambda x: x["score"])

    recommendations = [rec for process in analysed for rec in process["recommendations"]]
    recommendations.sort(key=lambda x: (x["priority"], x["confidence"]), reverse=True)
    scores = [item["score"] for item in analysed]

    return {
        "version": VERSION,
        "status": "ok" if analysed else "insufficient_data",
        "overall_score": round(sum(scores) / len(scores), 1) if scores else None,
        "summary": {
            "processes_analyzed": len(analysed),
            "optimized": sum(1 for item in analysed if item["status"] == "optimized"),
            "improvable": sum(1 for item in analysed if item["status"] == "improvable"),
            "redesign": sum(1 for item in analysed if item["status"] == "redesign"),
            "recommendations": len(recommendations),
            "process_mining_patterns": len(process_mining.get("automation_candidates") or []),
            "handoff_routes": len(process_mining.get("handoff_routes") or []),
            "bottlenecks": len(process_mining.get("bottlenecks") or []),
        },
        "processes": analysed,
        "top_recommendations": recommendations[:10],
        "methodology": (
            "Process Mining нормализуется в повторяющиеся рабочие паттерны и маршруты передачи; "
            "дополнительно используются Business Architecture и Deep REST Evidence. "
            "Отсутствующий показатель не считается подтверждённой проблемой. Groq не участвует в расчёте score."
        ),
    }
