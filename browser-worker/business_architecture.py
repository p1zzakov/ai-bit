from __future__ import annotations

import asyncio
import json
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from operational_intelligence import fetch_all, rest_call

VERSION = "1.0.0-rc.1"
DEAL_ENTITY_TYPE_ID = 2
DOCUMENT_WORDS = (
    "договор", "счет", "счёт", "акт", "наклад", "заяв", "приказ", "служеб", "документ",
    "согласован", "подпис", "регистрац", "архив", "коммерческ", "кп",
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def _status(score: int, evidence: int) -> str:
    if evidence == 0:
        return "insufficient_data"
    if score >= 85:
        return "mature"
    if score >= 70:
        return "ready"
    if score >= 50:
        return "needs_optimization"
    if score >= 25:
        return "partially_ready"
    return "not_ready"


def _recommend(severity: str, title: str, finding: str, action: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "severity": severity,
        "title": title,
        "finding": finding,
        "action": action,
        "evidence": evidence,
    }


async def _safe_call(webhook: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        data = await rest_call(webhook, method, params or {})
        return {"method": method, "ok": True, "result": data.get("result"), "total": data.get("total")}
    except Exception as exc:  # Bitrix editions and permissions differ
        return {"method": method, "ok": False, "error": str(exc)[:600], "result": None}


async def _safe_all(webhook: str, method: str, params: dict[str, Any] | None = None, limit: int = 5000) -> dict[str, Any]:
    try:
        rows = await fetch_all(webhook, method, params or {}, limit=limit)
        return {"method": method, "ok": True, "rows": rows, "count": len(rows)}
    except Exception as exc:
        return {"method": method, "ok": False, "error": str(exc)[:600], "rows": [], "count": 0}


def _extract_rows(call: dict[str, Any]) -> list[dict[str, Any]]:
    result = call.get("result")
    if isinstance(result, list):
        return [x for x in result if isinstance(x, dict)]
    if isinstance(result, dict):
        for key in ("items", "templates", "workflows", "categories", "stages"):
            value = result.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _audit_business_processes(template_call: dict[str, Any], workflow_call: dict[str, Any]) -> dict[str, Any]:
    templates = _extract_rows(template_call)
    workflows = _extract_rows(workflow_call)
    recs: list[dict[str, Any]] = []
    evidence = int(template_call.get("ok", False)) + int(workflow_call.get("ok", False))

    active = 0
    ownerless = 0
    undocumented = 0
    template_rows: list[dict[str, Any]] = []
    for item in templates:
        name = str(item.get("NAME") or item.get("name") or item.get("TITLE") or "Без названия")
        active_flag = str(item.get("ACTIVE", item.get("active", "Y"))).upper() not in {"N", "FALSE", "0"}
        if active_flag:
            active += 1
        description = str(item.get("DESCRIPTION") or item.get("description") or "").strip()
        owner = item.get("MODIFIED_BY") or item.get("CREATED_BY") or item.get("owner")
        if not owner:
            ownerless += 1
        if not description:
            undocumented += 1
        template_rows.append({
            "id": str(item.get("ID") or item.get("id") or ""),
            "name": name,
            "active": active_flag,
            "document_type": item.get("DOCUMENT_TYPE") or item.get("documentType"),
            "description_present": bool(description),
            "owner_present": bool(owner),
        })

    running = 0
    stalled = 0
    completed = 0
    for item in workflows:
        status = str(item.get("STATUS") or item.get("status") or "").lower()
        if status in {"completed", "5", "finished"}:
            completed += 1
        else:
            running += 1
        if status in {"stalled", "error", "4"} or item.get("ERROR"):
            stalled += 1

    readiness = _clamp(30 + min(40, len(templates) * 4) + (15 if active else 0) + (15 if evidence == 2 else 0)) if evidence else 0
    architecture = _clamp(85 - ownerless * 8 - undocumented * 5) if templates else 0
    efficiency = _clamp(80 - stalled * 8 - (20 if workflows and completed == 0 else 0)) if workflows else 0
    automation = _clamp(35 + min(60, len(templates) * 5)) if templates else 0
    score = _clamp(readiness * .3 + architecture * .25 + efficiency * .3 + automation * .15) if evidence else 0

    if not templates:
        recs.append(_recommend("high", "Шаблоны бизнес-процессов не подтверждены", "REST не вернул доступные шаблоны процессов.", "Проверить права webhook и наличие активных шаблонов. Не считать контур готовым до получения evidence.", [template_call.get("method", "")]))
    if undocumented:
        recs.append(_recommend("medium", "Процессы без описания", f"У {undocumented} шаблонов отсутствует описание назначения.", "Зафиксировать цель, владельца, входы, выходы, SLA и исключения для каждого процесса.", ["bizproc templates"] ))
    if ownerless:
        recs.append(_recommend("high", "Не определены владельцы процессов", f"У {ownerless} шаблонов не удалось подтвердить владельца.", "Назначить бизнес-владельца и технического ответственного, определить порядок изменений.", ["bizproc templates"] ))
    if stalled:
        recs.append(_recommend("high", "Есть зависшие или ошибочные экземпляры", f"Обнаружено {stalled} проблемных запусков.", "Добавить SLA, эскалацию, обработку ошибок и регулярный контроль зависших экземпляров.", ["bizproc workflows"] ))

    return {
        "score": score,
        "status": _status(score, evidence),
        "evidence_status": "complete" if evidence == 2 else "partial" if evidence else "missing",
        "scores": {"readiness": readiness, "architecture": architecture, "efficiency": efficiency, "automation": automation},
        "summary": {"templates": len(templates), "active_templates": active, "running_instances": running, "completed_instances": completed, "stalled_instances": stalled},
        "items": template_rows,
        "recommendations": recs,
        "sources": [template_call, workflow_call],
    }


def _deal_stage_id(deal: dict[str, Any]) -> str:
    return str(deal.get("STAGE_ID") or deal.get("stageId") or "UNKNOWN")


def _audit_crm(categories_call: dict[str, Any], status_call: dict[str, Any], deals_call: dict[str, Any]) -> dict[str, Any]:
    categories = _extract_rows(categories_call)
    statuses = _extract_rows(status_call)
    deals = deals_call.get("rows", []) if deals_call.get("ok") else []
    evidence = sum(int(x.get("ok", False)) for x in (categories_call, status_call, deals_call))
    recs: list[dict[str, Any]] = []

    stages = [x for x in statuses if "DEAL_STAGE" in str(x.get("ENTITY_ID") or x.get("entityId") or "")]
    stage_counts = Counter(_deal_stage_id(x) for x in deals)
    no_responsible = sum(1 for x in deals if not (x.get("ASSIGNED_BY_ID") or x.get("assignedById")))
    no_source = sum(1 for x in deals if not (x.get("SOURCE_ID") or x.get("sourceId")))
    no_amount = sum(1 for x in deals if _num(x.get("OPPORTUNITY") or x.get("opportunity")) <= 0)
    no_activity = sum(1 for x in deals if str(x.get("CLOSED") or x.get("closed") or "N").upper() != "Y" and not (x.get("LAST_ACTIVITY_TIME") or x.get("lastActivityTime")))
    unused_stages = [x for x in stages if stage_counts.get(str(x.get("STATUS_ID") or x.get("statusId") or ""), 0) == 0]

    category_rows = []
    for c in categories:
        category_rows.append({
            "id": str(c.get("id") or c.get("ID") or "0"),
            "name": c.get("name") or c.get("NAME") or "Основная",
            "is_default": bool(c.get("isDefault") or c.get("IS_DEFAULT")),
        })

    data_quality = _clamp(100 - (no_responsible + no_source + no_amount) * 100 / max(1, len(deals) * 3)) if deals else 0
    architecture = _clamp(95 - max(0, len(stages) - max(10, len(categories) * 10)) * 3 - len(unused_stages) * 4) if stages else 0
    readiness = _clamp(30 + min(25, len(categories) * 10) + min(30, len(stages) * 2) + (15 if deals else 0)) if evidence else 0
    efficiency = _clamp(90 - no_activity * 100 / max(1, len(deals)) - len(unused_stages) * 3) if deals else 0
    automation = _clamp(35 + (10 if stages else 0)) if evidence else 0
    score = _clamp(readiness * .2 + architecture * .25 + data_quality * .25 + efficiency * .2 + automation * .1) if evidence else 0

    if len(stages) > max(14, len(categories) * 12):
        recs.append(_recommend("medium", "Слишком детальная структура стадий", f"Обнаружено {len(stages)} стадий на {max(1, len(categories))} воронок.", "Проверить дублирование стадий и оставить только этапы, меняющие ответственность, обязательные данные или управленческое решение.", ["crm.status.list"] ))
    if unused_stages:
        recs.append(_recommend("medium", "Неиспользуемые стадии", f"Не найдено сделок в {len(unused_stages)} стадиях.", "Проверить необходимость стадий, архивировать лишние или настроить корректное продвижение сделок.", ["crm.status.list", "crm.deal.list"] ))
    if no_responsible:
        recs.append(_recommend("high", "Сделки без ответственного", f"Обнаружено {no_responsible} сделок без подтверждённого ответственного.", "Запретить создание сделки без ответственного и настроить автоматическое распределение.", ["crm.deal.list"] ))
    if no_source:
        recs.append(_recommend("medium", "Не заполнены источники", f"У {no_source} сделок отсутствует источник.", "Сделать источник обязательным либо заполнять автоматически из канала обращения.", ["crm.deal.list"] ))
    if no_activity:
        recs.append(_recommend("high", "Нет следующей активности", f"У {no_activity} открытых сделок не подтверждена активность.", "Настроить обязательное следующее действие, робота контроля и эскалацию зависших сделок.", ["crm.deal.list"] ))

    return {
        "score": score,
        "status": _status(score, evidence),
        "evidence_status": "complete" if evidence == 3 else "partial" if evidence else "missing",
        "scores": {"readiness": readiness, "architecture": architecture, "data_quality": data_quality, "efficiency": efficiency, "automation": automation},
        "summary": {"funnels": max(1, len(categories)) if evidence else 0, "stages": len(stages), "deals_analyzed": len(deals), "deals_without_responsible": no_responsible, "deals_without_source": no_source, "deals_without_amount": no_amount, "deals_without_activity": no_activity, "unused_stages": len(unused_stages)},
        "funnels": category_rows,
        "stage_distribution": dict(stage_counts),
        "recommendations": recs,
        "sources": [categories_call, status_call, {k: v for k, v in deals_call.items() if k != "rows"}],
    }


def _audit_documents(templates_call: dict[str, Any], operations: dict[str, Any] | None, crawl: dict[str, Any] | None) -> dict[str, Any]:
    templates = _extract_rows(templates_call)
    task_events = (operations or {}).get("task_events", [])
    document_tasks = [x for x in task_events if any(word in str(x.get("title", "")).lower() for word in DOCUMENT_WORDS)]
    pages = (crawl or {}).get("nodes", [])
    document_pages = [x for x in pages if any(word in (str(x.get("title", "")) + " " + str(x.get("url", ""))).lower() for word in DOCUMENT_WORDS)]
    evidence = int(templates_call.get("ok", False)) + int(bool(operations)) + int(bool(crawl))
    recs: list[dict[str, Any]] = []

    without_deadline = sum(1 for x in document_tasks if not x.get("deadline"))
    overdue = sum(1 for x in document_tasks if x.get("overdue"))
    repeated_titles = Counter(str(x.get("normalized_title") or x.get("title") or "") for x in document_tasks)
    repeated = sum(1 for _, count in repeated_titles.items() if count >= 3)

    readiness = _clamp(20 + min(35, len(templates) * 5) + min(25, len(document_pages) * 3) + (20 if document_tasks else 0)) if evidence else 0
    architecture = _clamp(75 - without_deadline * 2 - (15 if document_tasks and not templates else 0)) if document_tasks or templates else 0
    efficiency = _clamp(90 - overdue * 5 - without_deadline * 2) if document_tasks else 0
    automation = _clamp(25 + min(60, len(templates) * 7) + min(15, repeated * 3)) if evidence else 0
    governance = _clamp(70 if templates and document_pages else 45 if templates or document_pages else 0)
    score = _clamp(readiness * .2 + architecture * .2 + efficiency * .2 + automation * .2 + governance * .2) if evidence else 0

    if document_tasks and not templates:
        recs.append(_recommend("high", "Документооборот выполняется задачами без подтверждённого маршрута", f"Найдено {len(document_tasks)} документных задач, но шаблоны согласования не подтверждены.", "Создать типовые карточки и маршруты документов вместо ручной передачи задач и файлов.", ["task events", templates_call.get("method", "")]))
    if without_deadline:
        recs.append(_recommend("high", "Документные задачи без срока", f"У {without_deadline} задач, связанных с документами, отсутствует deadline.", "Установить SLA по типам документов и автоматическую эскалацию просрочки.", ["task events"] ))
    if overdue:
        recs.append(_recommend("high", "Просрочка в документообороте", f"Обнаружено {overdue} просроченных документных задач.", "Найти этапы ожидания, внедрить заместителей, таймеры и уведомления владельцу процесса.", ["task events"] ))
    if repeated:
        recs.append(_recommend("medium", "Повторяющиеся документные операции", f"Обнаружено {repeated} устойчивых шаблонов повторяющихся задач.", "Перенести повторяющиеся операции в шаблоны, смарт-процессы или бизнес-процессы с единой карточкой документа.", ["process mining task events"] ))
    if not document_pages:
        recs.append(_recommend("medium", "Не подтверждена единая точка работы с документами", "Crawler не обнаружил специализированные страницы или формы документооборота.", "Проверить наличие реестров, карточек документов, единой структуры хранения и понятной навигации.", ["browser crawl"] ))

    return {
        "score": score,
        "status": _status(score, evidence),
        "evidence_status": "complete" if evidence == 3 else "partial" if evidence else "missing",
        "scores": {"readiness": readiness, "architecture": architecture, "efficiency": efficiency, "automation": automation, "governance": governance},
        "summary": {"workflow_templates": len(templates), "document_tasks": len(document_tasks), "overdue_document_tasks": overdue, "without_deadline": without_deadline, "repeated_patterns": repeated, "document_pages": len(document_pages)},
        "recommendations": recs,
        "sources": [templates_call, {"source": "operations", "available": bool(operations)}, {"source": "crawl", "available": bool(crawl)}],
    }


async def collect_business_architecture(artifacts_dir: Path, operations: dict[str, Any] | None = None, crawl: dict[str, Any] | None = None) -> dict[str, Any]:
    webhook = os.getenv("BITRIX_WEBHOOK_URL", "").strip()
    if not webhook:
        raise RuntimeError("BITRIX_WEBHOOK_URL is not configured")

    template_call, workflow_call, categories_call, status_call, deals_call = await asyncio.gather(
        _safe_call(webhook, "bizproc.workflow.template.list", {}),
        _safe_call(webhook, "bizproc.workflow.instances", {}),
        _safe_call(webhook, "crm.category.list", {"entityTypeId": DEAL_ENTITY_TYPE_ID}),
        _safe_call(webhook, "crm.status.list", {}),
        _safe_all(webhook, "crm.deal.list", {"select[]": ["ID", "TITLE", "CATEGORY_ID", "STAGE_ID", "ASSIGNED_BY_ID", "SOURCE_ID", "OPPORTUNITY", "CLOSED", "LAST_ACTIVITY_TIME", "DATE_CREATE", "DATE_MODIFY"], "order[ID]": "asc"}, limit=20000),
    )

    business_processes = _audit_business_processes(template_call, workflow_call)
    crm = _audit_crm(categories_call, status_call, deals_call)
    documents = _audit_documents(template_call, operations, crawl)
    scores = [business_processes["score"], crm["score"], documents["score"]]
    evidence_ready = sum(1 for x in (business_processes, crm, documents) if x["evidence_status"] != "missing")
    enterprise_health = _clamp(sum(scores) / len(scores)) if evidence_ready else 0

    recommendations = []
    for domain, result in (("business_processes", business_processes), ("crm", crm), ("documents", documents)):
        for rec in result["recommendations"]:
            recommendations.append({"domain": domain, **rec})
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    recommendations.sort(key=lambda x: severity_rank.get(x.get("severity", "low"), 0), reverse=True)

    result = {
        "version": VERSION,
        "generated_at": _now(),
        "enterprise_health": enterprise_health,
        "status": _status(enterprise_health, evidence_ready),
        "domains": {"business_processes": business_processes, "crm": crm, "documents": documents},
        "summary": {
            "domains_ready": evidence_ready,
            "business_process_score": business_processes["score"],
            "crm_score": crm["score"],
            "document_score": documents["score"],
            "critical_recommendations": sum(1 for x in recommendations if x["severity"] in {"critical", "high"}),
        },
        "recommendations": recommendations,
        "methodology": "Каждая оценка разделяет готовность, архитектуру, автоматизацию, качество данных и фактическую эффективность. При недостатке REST/Browser evidence система возвращает partial или insufficient_data, а не делает положительный вывод.",
    }

    root = artifacts_dir / "business-architecture"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"business-architecture-{stamp}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["artifact"] = str(path)
    return result


def read_latest_business_architecture(artifacts_dir: Path) -> dict[str, Any]:
    path = artifacts_dir / "business-architecture" / "latest.json"
    if not path.exists():
        raise FileNotFoundError("No business architecture audit")
    return json.loads(path.read_text(encoding="utf-8"))
