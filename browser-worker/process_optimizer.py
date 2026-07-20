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


def _collect_processes(*sources: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    name_keys = ("name", "title", "process", "process_name", "workflow", "template_name")
    signal_keys = {
        "stages", "steps", "stage_count", "step_count", "duration", "duration_hours",
        "average_duration", "avg_duration", "executions", "runs", "instances",
        "automation", "robots", "triggers", "sla", "participants", "owners",
    }

    for source in sources:
        for node in _walk(source):
            if not isinstance(node, dict):
                continue
            lowered_keys = {str(k).lower() for k in node}
            if not lowered_keys.intersection(signal_keys):
                continue
            name = _first_text(node, name_keys)
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(node)
    return candidates


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
    name = _first_text(item, ("name", "title", "process", "process_name", "workflow", "template_name")) or f"Процесс {index}"
    process_id = _first_text(item, ("id", "process_id", "template_id", "workflow_id")) or f"process-{index}"
    stages = _first_number(item, ("stage_count", "step_count", "stages_count", "steps_count", "stages", "steps"))
    avg_hours = _first_number(item, ("average_duration_hours", "avg_duration_hours", "duration_hours", "average_duration", "avg_duration"))
    runs = _first_number(item, ("executions", "runs", "instances", "items", "count"))
    robots = _first_number(item, ("robots", "robot_count", "automation_rules"))
    triggers = _first_number(item, ("triggers", "trigger_count"))
    manual = _first_number(item, ("manual_actions", "manual_steps", "human_tasks"))
    loops = _first_number(item, ("loops", "cycles", "returns", "backward_transitions"))
    errors = _first_number(item, ("errors", "failed", "failed_runs", "error_count"))
    participants = _first_number(item, ("participants", "participant_count", "owners", "assignees"))
    sla = bool(item.get("sla") or item.get("deadline") or item.get("time_limit") or item.get("target_duration"))

    score = 100.0
    recommendations: list[dict[str, Any]] = []
    evidence: list[str] = []

    if stages:
        evidence.append(f"Обнаружено этапов: {int(stages)}")
    if avg_hours:
        evidence.append(f"Средняя длительность: {avg_hours:.1f} ч")
    if runs:
        evidence.append(f"Подтверждённых запусков: {int(runs)}")

    if stages > 9:
        penalty = min(24, (stages - 9) * 3)
        score -= penalty
        recommendations.append(_recommendation(
            process_id, name, f"Маршрут содержит {int(stages)} этапов.",
            "Провести функциональный разбор этапов, объединить дублирующие проверки и оставить только контрольные точки, влияющие на решение.",
            "Сокращение времени прохождения и количества передач между участниками.", 88, "excessive_steps", 86,
            [f"Количество этапов: {int(stages)}"],
        ))

    if loops > 0:
        score -= min(22, loops * 6)
        recommendations.append(_recommendation(
            process_id, name, f"Обнаружены возвраты или циклические переходы: {int(loops)}.",
            "Разделить возврат на исправление и повторное согласование, зафиксировать причины возврата и исключить повторное прохождение уже подтверждённых этапов.",
            "Снижение повторной работы и количества повторных согласований.", 93, "loops", 96,
            [f"Циклические/обратные переходы: {int(loops)}"],
        ))

    if runs > 0 and robots + triggers == 0:
        score -= 16
        recommendations.append(_recommendation(
            process_id, name, "Процесс используется, но подтверждённая автоматизация не обнаружена.",
            "Автоматизировать постановку типовых задач, уведомления, контроль сроков и переходы, не требующие управленческого решения.",
            "Сокращение ручных операций и зависимости от дисциплины участников.", 82, "low_automation", 82,
            [f"Запуски: {int(runs)}", "Роботы и триггеры не подтверждены"],
        ))

    if manual >= 4:
        score -= min(18, manual * 2)
        recommendations.append(_recommendation(
            process_id, name, f"Подтверждено ручных действий: {int(manual)}.",
            "Разделить действия на решения и механические операции; механические операции перенести в роботов, правила и автозаполнение.",
            "Снижение трудозатрат и числа ошибок ввода.", 86, "manual_work", 84,
            [f"Ручные действия: {int(manual)}"],
        ))

    if avg_hours >= 72 and not sla:
        score -= 15
        recommendations.append(_recommendation(
            process_id, name, f"Средняя длительность составляет {avg_hours / 24:.1f} дня, контрольный срок не подтверждён.",
            "Установить SLA процесса и этапов, предупреждение до нарушения срока и эскалацию владельцу процесса.",
            "Повышение прогнозируемости сроков и раннее выявление задержек.", 89, "missing_sla", 90,
            [f"Средняя длительность: {avg_hours:.1f} ч", "SLA не подтверждён"],
        ))

    if errors > 0:
        score -= min(20, errors * 3)
        recommendations.append(_recommendation(
            process_id, name, f"Обнаружены ошибки выполнения: {int(errors)}.",
            "Выделить типовые причины ошибок, добавить валидацию обязательных данных и контроль отказавших роботов.",
            "Снижение числа остановленных экземпляров и ручного восстановления.", 94, "execution_errors", 98,
            [f"Ошибки выполнения: {int(errors)}"],
        ))

    if participants == 1 and runs >= 3:
        score -= 12
        recommendations.append(_recommendation(
            process_id, name, "Исполнение процесса связано с одним подтверждённым участником.",
            "Назначить роль или группу вместо конкретного сотрудника, определить замещение и владельца процесса.",
            "Снижение зависимости от одного сотрудника и риска остановки процесса.", 80, "single_point_dependency", 78,
            ["Один подтверждённый участник", f"Запуски: {int(runs)}"],
        ))

    if runs == 0:
        score = min(score, 55)
        recommendations.append(_recommendation(
            process_id, name, "Фактические запуски процесса не подтверждены.",
            "Проверить, введён ли процесс в эксплуатацию, доступен ли пользователям и не дублируется ли работа вне Bitrix24.",
            "Исключение формально настроенных, но не используемых процессов.", 72, "unused_process", 70,
            ["Запуски не подтверждены"],
        ))

    score = round(max(0.0, min(100.0, score)), 1)
    status = "optimized" if score >= 80 else "improvable" if score >= 60 else "redesign"
    recommendations.sort(key=lambda x: x["priority"], reverse=True)

    return {
        "id": process_id,
        "name": name,
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
        },
        "processes": analysed,
        "top_recommendations": recommendations[:10],
        "methodology": (
            "Оценка построена только по доступным артефактам Process Mining, Business Architecture и Deep REST Evidence. "
            "Отсутствующий показатель не считается подтверждённой проблемой. Groq не участвует в расчёте score."
        ),
    }
