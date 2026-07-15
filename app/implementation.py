from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(prefix="/api/v1/implementation", tags=["implementation"])


STATUS_META = {
    "implemented": ("Внедрено и используется", "green"),
    "partial": ("Внедрено частично", "yellow"),
    "not_used": ("Не используется / не обнаружено", "red"),
    "manual": ("Требуется ручная проверка", "gray"),
}


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _latest_snapshot(reports_dir: Path) -> Path:
    candidates = sorted(
        (item for item in reports_dir.glob("audit-*") if item.is_dir()),
        key=lambda item: item.name,
        reverse=True,
    )
    if not candidates:
        raise HTTPException(status_code=404, detail="Сначала запустите /api/v1/audits/run")
    return candidates[0]


def _list(snapshot: Path, name: str) -> list[dict[str, Any]]:
    value = _load_json(snapshot / f"{name}.json", [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _dict(snapshot: Path, name: str) -> dict[str, Any]:
    value = _load_json(snapshot / f"{name}.json", {})
    return value if isinstance(value, dict) else {}


def _text(item: dict[str, Any], *keys: str) -> str:
    return " ".join(str(item.get(key, "")) for key in keys).strip().lower()


def _keyword_hits(items: list[dict[str, Any]], keys: tuple[str, ...], keywords: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for item in items:
        value = _text(item, *keys)
        if any(keyword in value for keyword in keywords):
            label = str(item.get("NAME") or item.get("name") or item.get("TITLE") or item.get("title") or item.get("ID") or "Объект")
            hits.append(label)
    return hits


def _module(
    code: str,
    title: str,
    status: str,
    evidence: list[str],
    missing: list[str],
    recommendation: str,
    effect: str,
    priority: int,
    confidence: str = "medium",
) -> dict[str, Any]:
    return {
        "code": code,
        "title": title,
        "status": status,
        "status_label": STATUS_META[status][0],
        "confidence": confidence,
        "evidence": evidence,
        "missing": missing,
        "recommendation": recommendation,
        "expected_effect": effect,
        "priority": priority,
    }


def assess_implementation(snapshot: Path, reports_dir: Path) -> dict[str, Any]:
    summary = _load_json(snapshot / "summary.json", {})
    explorer = _load_json(reports_dir / "latest-explorer.json", {})

    users = _list(snapshot, "users")
    departments = _list(snapshot, "departments")
    deals = _list(snapshot, "crm_deals")
    contacts = _list(snapshot, "crm_contacts")
    companies = _list(snapshot, "crm_companies")
    categories = _list(snapshot, "crm_categories")
    tasks = _list(snapshot, "tasks")
    groups = _list(snapshot, "groups")
    bizproc = _list(snapshot, "bizproc_templates")
    disk = _list(snapshot, "disk_storages")

    modules: list[dict[str, Any]] = []

    crm_evidence = [
        f"Сделок: {len(deals)}",
        f"Контактов: {len(contacts)}",
        f"Компаний: {len(companies)}",
        f"Воронок: {len(categories)}",
    ]
    crm_status = "implemented" if deals and (contacts or companies) and categories else "partial" if deals or categories else "not_used"
    modules.append(_module(
        "crm", "CRM и продажи", crm_status, crm_evidence,
        [] if crm_status == "implemented" else ["Не подтверждено полноценное использование сделок, клиентов и воронок"],
        "Сохранить CRM как основной контур продаж; отдельно проверить роботов, обязательные поля, источники лидов, отчёты и интеграцию с 1С.",
        "Единая управляемая воронка продаж и достоверная аналитика.", 2, "high",
    ))

    overdue = int(summary.get("facts", {}).get("overdue_tasks", 0) or 0)
    task_groups = {str(item.get("GROUP_ID") or item.get("groupId") or "0") for item in tasks}
    task_status = "implemented" if len(tasks) >= 50 and len(task_groups - {"0", ""}) >= 2 else "partial" if tasks else "not_used"
    modules.append(_module(
        "tasks", "Задачи и проекты", task_status,
        [f"Задач: {len(tasks)}", f"Просроченных: {overdue}", f"Задействовано групп/проектов: {len(task_groups - {'0', ''})}"],
        [] if task_status == "implemented" else ["Не подтверждено системное проектное использование"],
        "Утвердить правила постановки задач, шаблоны типовых работ, обязательные сроки и контроль просрочки по подразделениям.",
        "Прозрачность исполнения поручений и проектной работы.", 2, "high",
    ))

    doc_keywords = ("договор", "согласован", "документ", "счет", "счёт", "служеб", "приказ", "заявк", "акт ")
    doc_hits = _keyword_hits(bizproc, ("NAME", "name", "DOCUMENT_TYPE", "MODULE_ID"), doc_keywords)
    if len(doc_hits) >= 3:
        doc_status = "implemented"
    elif doc_hits or bizproc:
        doc_status = "partial"
    else:
        doc_status = "not_used"
    modules.append(_module(
        "document_management", "Документооборот и согласования", doc_status,
        [f"Шаблонов бизнес-процессов: {len(bizproc)}"] + (["Найдены признаки: " + ", ".join(doc_hits[:8])] if doc_hits else []),
        [] if doc_hits else ["Не обнаружены подтверждённые маршруты согласования договоров, счетов, служебных записок и приказов"],
        "Провести реестр документов и настроить приоритетные маршруты: договоры, счета на оплату, заявки, служебные записки и приказы. Для каждого маршрута назначить владельца и SLA.",
        "Сокращение сроков согласования, прозрачность ответственности и единый архив решений.", 1, "medium",
    ))

    service_keywords = ("service desk", "helpdesk", "техподдерж", "поддержк", "ит заяв", "it заяв", "сервис", "инцидент", "тикет")
    service_group_hits = _keyword_hits(groups, ("NAME", "name", "DESCRIPTION", "description"), service_keywords)
    service_task_hits = _keyword_hits(tasks, ("TITLE", "title", "DESCRIPTION", "description"), service_keywords)
    service_hits = service_group_hits + service_task_hits
    service_status = "implemented" if len(service_hits) >= 10 else "partial" if service_hits else "not_used"
    modules.append(_module(
        "service_desk", "Service Desk / внутренние заявки", service_status,
        ([f"Найдено признаков сервисных обращений: {len(service_hits)}"] + (["Примеры: " + ", ".join(service_hits[:6])] if service_hits else [])),
        [] if service_hits else ["Не обнаружены очередь обращений, категории, SLA и устойчивый поток тикетов"],
        "Настроить единый сервис заявок минимум для IT, АХО и HR: каталог услуг, категории, приоритеты, SLA, ответственные очереди и отчётность.",
        "Снижение потерь обращений, измеримое качество внутреннего сервиса и контроль загрузки специалистов.", 1, "medium",
    ))

    knowledge_keywords = ("база знаний", "knowledge", "инструкц", "регламент", "faq", "wiki")
    knowledge_hits = _keyword_hits(groups + tasks, ("NAME", "name", "TITLE", "title", "DESCRIPTION", "description"), knowledge_keywords)
    knowledge_status = "partial" if knowledge_hits else "not_used"
    modules.append(_module(
        "knowledge_base", "База знаний", knowledge_status,
        (["Найдены признаки: " + ", ".join(knowledge_hits[:8])] if knowledge_hits else []),
        [] if knowledge_hits else ["Через доступные данные не обнаружена системная корпоративная база знаний"],
        "Создать структуру базы знаний по подразделениям: IT-инструкции, регламенты, адаптация сотрудников, шаблоны документов и FAQ. Назначить владельцев и период актуализации.",
        "Сокращение повторных обращений и зависимости от отдельных сотрудников.", 2, "low",
    ))

    heads_missing = sum(1 for item in departments if not item.get("UF_HEAD"))
    hr_keywords = ("отпуск", "командиров", "адаптац", "увольнен", "прием", "приём", "кадр", "обучен")
    hr_hits = _keyword_hits(bizproc + tasks, ("NAME", "name", "TITLE", "title", "DESCRIPTION", "description"), hr_keywords)
    hr_status = "implemented" if users and departments and len(hr_hits) >= 3 and heads_missing == 0 else "partial" if users and departments else "not_used"
    modules.append(_module(
        "hr", "HR и жизненный цикл сотрудника", hr_status,
        [f"Сотрудников: {len(users)}", f"Подразделений: {len(departments)}", f"Подразделений без руководителя: {heads_missing}"] + (["HR-процессы: " + ", ".join(hr_hits[:6])] if hr_hits else []),
        ([f"Не назначены руководители в {heads_missing} подразделениях"] if heads_missing else []) + ([] if hr_hits else ["Не подтверждены процессы адаптации, отпусков, командировок и обучения"]),
        "Актуализировать оргструктуру, затем внедрить приоритетные HR-процессы: отпуск, командировка, адаптация, обучение и увольнение.",
        "Корректная маршрутизация согласований и снижение ручной нагрузки HR.", 1, "high",
    ))

    explorer_modules = explorer.get("modules", {}) if isinstance(explorer, dict) else {}
    communication_specs = [
        ("telephony", "Телефония", "telephony", "Проверить маршрутизацию, запись звонков, привязку к CRM и отчёты по пропущенным звонкам."),
        ("openlines", "Открытые линии", "openlines", "Подключить приоритетные цифровые каналы, распределение обращений, очереди и контроль времени ответа."),
        ("mail", "Почта в Битрикс24", "mail", "Проверить подключение корпоративных ящиков, автоматическую привязку переписки к CRM и права доступа."),
        ("rpa", "RPA / смарт-процессы", "rpa", "Определить процессы, которые целесообразно перенести в смарт-процессы: заявки, закупки, договоры и внутренние согласования."),
    ]
    for code, title, explorer_code, recommendation in communication_specs:
        stats = explorer_modules.get(explorer_code, {}) if isinstance(explorer_modules, dict) else {}
        available = int(stats.get("ok", 0) or 0) > 0
        modules.append(_module(
            code, title, "manual" if available else "not_used",
            ["REST-раздел доступен"] if available else [],
            ["Наличие настройки не подтверждает фактическое использование; требуется проверка конфигурации и статистики"],
            recommendation,
            "Повышение управляемости коммуникаций и автоматизации.", 3, "low",
        ))

    modules.append(_module(
        "bi", "BI и управленческая аналитика", "manual", [],
        ["REST-снимок не подтверждает наличие согласованных управленческих дашбордов и регулярного использования BI"],
        "Согласовать KPI руководства и настроить дашборды по продажам, просроченным задачам, срокам согласования и загрузке подразделений.",
        "Единая управленческая картина и контроль эффекта от внедрения.", 3, "low",
    ))

    counts = Counter(item["status"] for item in modules)
    evaluated = counts["implemented"] + counts["partial"] + counts["not_used"]
    score = round((counts["implemented"] + counts["partial"] * 0.5) * 100 / evaluated) if evaluated else 0
    roadmap = sorted(
        [item for item in modules if item["status"] in {"not_used", "partial"}],
        key=lambda item: (item["priority"], 0 if item["status"] == "not_used" else 1, item["title"]),
    )

    return {
        "generated_at": summary.get("generated_at") or snapshot.name,
        "source_snapshot": snapshot.name,
        "read_only": True,
        "score": score,
        "counts": dict(counts),
        "modules": modules,
        "roadmap": roadmap,
        "disclaimer": "Статусы основаны только на доступных REST-данных. При недостатке доказательств используется статус 'Требуется ручная проверка', а не предположение о наличии настройки.",
    }


def render_report(result: dict[str, Any]) -> str:
    cards = []
    for module in result["modules"]:
        label, color = STATUS_META[module["status"]]
        evidence = "".join(f"<li>{html.escape(value)}</li>" for value in module["evidence"]) or "<li>Автоматические подтверждения отсутствуют</li>"
        missing = "".join(f"<li>{html.escape(value)}</li>" for value in module["missing"])
        cards.append(
            f"<section class='module'><div class='module-head'><h2>{html.escape(module['title'])}</h2><span class='badge {color}'>{html.escape(label)}</span></div>"
            f"<div class='columns'><div><h3>Что подтверждено</h3><ul>{evidence}</ul></div>"
            f"<div><h3>Что отсутствует или требует проверки</h3><ul>{missing or '<li>Критичные пробелы автоматически не обнаружены</li>'}</ul></div></div>"
            f"<div class='recommend'><b>Рекомендуется:</b> {html.escape(module['recommendation'])}<br><b>Ожидаемый эффект:</b> {html.escape(module['expected_effect'])}</div></section>"
        )

    roadmap_rows = "".join(
        f"<tr><td>{index}</td><td>{html.escape(item['title'])}</td><td>{html.escape(STATUS_META[item['status']][0])}</td><td>{html.escape(item['recommendation'])}</td></tr>"
        for index, item in enumerate(result["roadmap"][:10], 1)
    )
    counts = result["counts"]
    return f"""<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Аудит внедрения Битрикс24</title><style>
body{{font-family:Arial,sans-serif;margin:0;background:#f3f5f7;color:#20242a}}main{{max-width:1250px;margin:28px auto;padding:0 20px}}header,.module,.roadmap{{background:#fff;border-radius:12px;padding:24px;margin-bottom:18px;box-shadow:0 2px 12px #00000010}}
h1,h2,h3{{margin-top:0}}.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:20px}}.metric{{background:#f7f9fb;border-radius:10px;padding:16px}}.metric b{{font-size:28px;display:block}}
.module-head{{display:flex;justify-content:space-between;gap:16px;align-items:center}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.badge{{padding:7px 11px;border-radius:999px;font-weight:bold;white-space:nowrap}}.green{{background:#dff7e8;color:#176b3a}}.yellow{{background:#fff1c7;color:#765600}}.red{{background:#ffe0e0;color:#962929}}.gray{{background:#e8edf2;color:#4e5965}}
.recommend{{background:#f7f9fb;border-left:4px solid #5b6b7c;padding:14px;margin-top:12px;line-height:1.55}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid #e4e8ec;text-align:left;vertical-align:top}}th{{background:#f8fafb}}.muted{{color:#68717d}}@media(max-width:760px){{.columns{{grid-template-columns:1fr}}.module-head{{align-items:flex-start;flex-direction:column}}}}
</style></head><body><main><header><h1>Аудит внедрения Битрикс24</h1><p class='muted'>Отдельный бизнес-отчёт. Источник: {html.escape(result['source_snapshot'])}. Режим: строго только чтение.</p>
<div class='summary'><div class='metric'><b>{result['score']}%</b>предварительная зрелость</div><div class='metric'><b>{counts.get('implemented',0)}</b>внедрено</div><div class='metric'><b>{counts.get('partial',0)}</b>частично</div><div class='metric'><b>{counts.get('not_used',0)}</b>не используется</div><div class='metric'><b>{counts.get('manual',0)}</b>проверить вручную</div></div></header>
{''.join(cards)}<section class='roadmap'><h2>Приоритетный план развития</h2><table><thead><tr><th>№</th><th>Модуль</th><th>Текущее состояние</th><th>Следующее действие</th></tr></thead><tbody>{roadmap_rows}</tbody></table></section>
<section class='roadmap'><h2>Ограничения оценки</h2><p>{html.escape(result['disclaimer'])}</p></section></main></body></html>"""


@router.post("/run")
async def implementation_run() -> dict[str, Any]:
    from app import main as core

    snapshot = _latest_snapshot(core.settings.reports_dir)
    result = assess_implementation(snapshot, core.settings.reports_dir)
    json_path = core.settings.reports_dir / "latest-implementation.json"
    html_path = core.settings.reports_dir / "latest-implementation.html"
    core.write_json(json_path, result)
    html_path.write_text(render_report(result), encoding="utf-8")
    return {
        "status": "completed",
        "read_only": True,
        "score": result["score"],
        "modules": len(result["modules"]),
        "report_url": "/api/v1/implementation/latest",
        "json_url": "/api/v1/implementation/latest/json",
    }


@router.get("/latest", response_class=HTMLResponse)
async def implementation_latest() -> FileResponse:
    from app import main as core

    path = core.settings.reports_dir / "latest-implementation.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Сначала запустите /api/v1/implementation/run")
    return FileResponse(path, media_type="text/html; charset=utf-8")


@router.get("/latest/json")
async def implementation_latest_json() -> Any:
    from app import main as core

    path = core.settings.reports_dir / "latest-implementation.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Сначала запустите /api/v1/implementation/run")
    return _load_json(path, {})
