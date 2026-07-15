from __future__ import annotations

import html
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "AI-BIT"
    bitrix_webhook_url: str = ""
    bitrix_verify_tls: bool = True
    bitrix_request_timeout: float = 30.0
    reports_dir: Path = Path("/app/reports")


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.3.0")


METHOD_CATALOG: list[dict[str, Any]] = [
    {"module": "core", "method": "profile", "mode": "one"},
    {"module": "core", "method": "scope", "mode": "one"},
    {"module": "company", "method": "user.get", "mode": "list"},
    {"module": "company", "method": "department.get", "mode": "list"},
    {"module": "crm", "method": "crm.category.list", "mode": "list", "params": {"entityTypeId": 2}, "result_key": "categories"},
    {"module": "crm", "method": "crm.status.list", "mode": "list"},
    {"module": "crm", "method": "crm.deal.fields", "mode": "one"},
    {"module": "crm", "method": "crm.contact.fields", "mode": "one"},
    {"module": "crm", "method": "crm.company.fields", "mode": "one"},
    {"module": "crm", "method": "crm.type.list", "mode": "list", "result_key": "types"},
    {"module": "crm", "method": "crm.deal.list", "mode": "list", "params": {"select": ["ID", "CATEGORY_ID", "STAGE_ID", "ASSIGNED_BY_ID", "DATE_CREATE"]}},
    {"module": "crm", "method": "crm.contact.list", "mode": "list", "params": {"select": ["ID", "ASSIGNED_BY_ID", "DATE_CREATE"]}},
    {"module": "crm", "method": "crm.company.list", "mode": "list", "params": {"select": ["ID", "ASSIGNED_BY_ID", "DATE_CREATE"]}},
    {"module": "tasks", "method": "tasks.task.fields", "mode": "one"},
    {"module": "tasks", "method": "tasks.task.list", "mode": "list", "params": {"select": ["ID", "TITLE", "STATUS", "DEADLINE", "RESPONSIBLE_ID", "GROUP_ID", "CREATED_DATE"]}, "result_key": "tasks"},
    {"module": "tasks", "method": "sonet_group.get", "mode": "list"},
    {"module": "bizproc", "method": "bizproc.workflow.template.list", "mode": "list"},
    {"module": "disk", "method": "disk.storage.getlist", "mode": "list"},
    {"module": "calendar", "method": "calendar.section.get", "mode": "one", "params": {"type": "user", "ownerId": 1}},
    {"module": "rpa", "method": "rpa.type.list", "mode": "list", "result_key": "types"},
    {"module": "openlines", "method": "imopenlines.config.list.get", "mode": "one"},
    {"module": "telephony", "method": "voximplant.line.get", "mode": "one"},
    {"module": "mail", "method": "mailservice.list", "mode": "one"},
    {"module": "apps", "method": "app.info", "mode": "one"},
]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


async def bitrix_call(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.bitrix_webhook_url:
        raise HTTPException(status_code=503, detail="BITRIX_WEBHOOK_URL is not configured")

    url = f"{settings.bitrix_webhook_url.rstrip('/')}/{method}.json"
    try:
        async with httpx.AsyncClient(timeout=settings.bitrix_request_timeout, verify=settings.bitrix_verify_tls) as client:
            response = await client.post(url, json=params or {})
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Bitrix24 request failed: {exc}") from exc

    if "error" in payload:
        raise HTTPException(
            status_code=502,
            detail=f"Bitrix24 API error: {payload['error']}: {payload.get('error_description', '')}",
        )
    return payload


def extract_items(result: Any, result_key: str | None = None) -> list[Any]:
    if result_key and isinstance(result, dict):
        value = result.get(result_key, [])
        return value if isinstance(value, list) else []
    if isinstance(result, list):
        return result
    return []


async def bitrix_list(
    method: str,
    params: dict[str, Any] | None = None,
    *,
    result_key: str | None = None,
    max_pages: int = 500,
) -> list[Any]:
    items: list[Any] = []
    start: int | str = 0
    base_params = dict(params or {})
    for _ in range(max_pages):
        payload = await bitrix_call(method, {**base_params, "start": start})
        items.extend(extract_items(payload.get("result"), result_key))
        if payload.get("next") is None:
            break
        start = payload["next"]
    return items


def object_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    return 1 if value is not None else 0


def sample_fields(value: Any) -> list[str]:
    sample = value[0] if isinstance(value, list) and value else value
    return sorted(str(key) for key in sample.keys()) if isinstance(sample, dict) else []


def active_users(users: list[Any]) -> int:
    def is_active(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().upper() in {"Y", "YES", "TRUE", "1"}

    return sum(1 for user in users if isinstance(user, dict) and is_active(user.get("ACTIVE", True)))


def departments_without_head(departments: list[Any]) -> int:
    return sum(1 for item in departments if isinstance(item, dict) and not item.get("UF_HEAD"))


def overdue_tasks(tasks: list[Any]) -> int:
    now = datetime.now(UTC)
    count = 0
    for task in tasks:
        if not isinstance(task, dict):
            continue
        deadline = task.get("deadline") or task.get("DEADLINE")
        status = str(task.get("status") or task.get("STATUS") or "").lower()
        if not deadline or status in {"4", "5", "6", "completed", "deferred"}:
            continue
        try:
            parsed = datetime.fromisoformat(str(deadline).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            if parsed < now:
                count += 1
        except ValueError:
            continue
    return count


def create_findings(collected: dict[str, Any]) -> list[dict[str, Any]]:
    users = collected.get("users", []) if isinstance(collected.get("users"), list) else []
    departments = collected.get("departments", []) if isinstance(collected.get("departments"), list) else []
    tasks = collected.get("tasks", []) if isinstance(collected.get("tasks"), list) else []
    deals = collected.get("crm_deals", []) if isinstance(collected.get("crm_deals"), list) else []
    categories = collected.get("crm_categories", []) if isinstance(collected.get("crm_categories"), list) else []
    deal_fields = collected.get("crm_deal_fields", {}) if isinstance(collected.get("crm_deal_fields"), dict) else {}

    findings: list[dict[str, Any]] = []
    missing_heads = departments_without_head(departments)
    if missing_heads:
        findings.append({
            "severity": "high",
            "area": "Оргструктура",
            "title": "Подразделения без назначенного руководителя",
            "observed": f"{missing_heads} из {len(departments)} подразделений",
            "impact": "Маршруты согласования, автоматическое определение руководителя и эскалации могут работать непредсказуемо.",
            "recommendation": "Сверить структуру с утверждённой оргсхемой и назначить UF_HEAD для каждого действующего подразделения.",
            "basis": "Функциональная best practice: оргструктура должна быть полной до запуска процессов согласования.",
            "basis_type": "expert",
        })

    overdue = overdue_tasks(tasks)
    overdue_pct = round(overdue * 100 / len(tasks), 1) if tasks else 0.0
    if overdue_pct >= 5:
        severity = "high" if overdue_pct >= 10 else "medium"
        findings.append({
            "severity": severity,
            "area": "Задачи",
            "title": "Повышенная доля просроченных незавершённых задач",
            "observed": f"{overdue} из {len(tasks)} задач ({overdue_pct}%)",
            "impact": "Сроки в системе перестают быть управленческим инструментом, отчётность по исполнению и эскалации теряют достоверность.",
            "recommendation": "Разобрать просрочку по подразделениям, закрыть устаревшие задачи, внедрить контроль сроков и регламент переноса дедлайнов.",
            "basis": "Экспертная эвристика: 5% — порог внимания, 10% — высокий риск дисциплины исполнения.",
            "basis_type": "heuristic",
        })

    custom_fields = sum(1 for key in deal_fields if str(key).startswith("UF_"))
    if custom_fields >= 100:
        severity = "high" if custom_fields >= 200 else "medium"
        findings.append({
            "severity": severity,
            "area": "CRM",
            "title": "Большое количество пользовательских полей сделок",
            "observed": f"{custom_fields} пользовательских полей",
            "impact": "Растут сложность карточки, стоимость сопровождения, риск дублей и ошибок в автоматизации.",
            "recommendation": "Сформировать реестр полей: владелец, назначение, заполненность, зависимости. Неиспользуемые поля архивировать после проверки роботов и бизнес-процессов.",
            "basis": "Экспертная эвристика; жёсткого официального лимита Bitrix24 нет.",
            "basis_type": "heuristic",
        })

    if len(categories) > 8:
        findings.append({
            "severity": "medium",
            "area": "CRM",
            "title": "Большое количество воронок сделок",
            "observed": f"{len(categories)} воронок",
            "impact": "Возможны дублирующие процессы, разные правила ведения сделок и усложнение аналитики.",
            "recommendation": "Для каждой воронки зафиксировать бизнес-владельца, назначение, вход/выход процесса и проверить фактическую активность.",
            "basis": "Экспертная эвристика; количество воронок должно соответствовать самостоятельным бизнес-процессам, а не отделам или отдельным сотрудникам.",
            "basis_type": "heuristic",
        })

    deals_by_category = Counter(str(item.get("CATEGORY_ID", "0")) for item in deals if isinstance(item, dict))
    empty_categories = [
        str(item.get("NAME") or item.get("name") or item.get("ID") or item.get("id"))
        for item in categories
        if isinstance(item, dict)
        and deals_by_category.get(str(item.get("ID") or item.get("id") or "0"), 0) == 0
    ]
    if empty_categories:
        findings.append({
            "severity": "medium",
            "area": "CRM",
            "title": "Воронки без сделок",
            "observed": ", ".join(empty_categories[:15]),
            "impact": "Пустые или тестовые воронки создают визуальный шум и могут вводить пользователей в заблуждение.",
            "recommendation": "Проверить назначение воронок; тестовые и устаревшие удалить либо скрыть после проверки автоматизаций.",
            "basis": "Функциональная best practice: каждая активная воронка должна иметь владельца и фактическое назначение.",
            "basis_type": "expert",
        })

    inactive = max(len(users) - active_users(users), 0)
    if users and inactive / len(users) >= 0.15:
        findings.append({
            "severity": "medium",
            "area": "Пользователи",
            "title": "Высокая доля неактивных учётных записей",
            "observed": f"{inactive} из {len(users)} пользователей",
            "impact": "Усложняется управление правами, лицензиями, ответственными и маршрутизацией задач.",
            "recommendation": "Сверить пользователей с кадровым списком, проверить владельцев CRM-объектов и корректно деактивировать устаревшие записи.",
            "basis": "Security and governance best practice: доступ должен соответствовать актуальному составу сотрудников.",
            "basis_type": "expert",
        })

    return findings


def severity_label(value: str) -> tuple[str, str]:
    return {
        "high": ("Высокий", "red"),
        "medium": ("Средний", "yellow"),
        "low": ("Низкий", "green"),
    }.get(value, ("Информация", "gray"))


def render_advisor_report(summary: dict[str, Any], findings: list[dict[str, Any]], explorer: dict[str, Any]) -> str:
    finding_rows = []
    for finding in findings:
        label, color = severity_label(finding["severity"])
        finding_rows.append(
            "<tr>"
            f"<td><span class='badge {color}'>{html.escape(label)}</span></td>"
            f"<td><b>{html.escape(finding['area'])}</b><br>{html.escape(finding['title'])}</td>"
            f"<td>{html.escape(finding['observed'])}</td>"
            f"<td>{html.escape(finding['impact'])}</td>"
            f"<td>{html.escape(finding['recommendation'])}<div class='basis'>{html.escape(finding['basis'])}</div></td>"
            "</tr>"
        )

    capability_rows = []
    for module, data in explorer.get("modules", {}).items():
        capability_rows.append(
            f"<tr><td>{html.escape(module)}</td><td>{data['ok']}</td><td>{data['failed']}</td><td>{data['coverage']}%</td></tr>"
        )

    return f"""<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Bitrix24 Best Practice Review</title><style>
body{{font-family:Arial,sans-serif;margin:0;background:#f3f5f7;color:#20242a}}main{{max-width:1400px;margin:28px auto;padding:0 20px}}
header,section{{background:#fff;border-radius:12px;padding:24px;margin-bottom:18px;box-shadow:0 2px 12px #00000010}}h1,h2{{margin-top:0}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:13px;border-bottom:1px solid #e4e8ec;text-align:left;vertical-align:top}}th{{background:#f8fafb}}
.badge{{display:inline-block;padding:6px 10px;border-radius:999px;font-weight:bold;font-size:13px}}.red{{background:#ffe0e0;color:#962929}}.yellow{{background:#fff1c7;color:#765600}}.green{{background:#dff7e8;color:#176b3a}}.gray{{background:#e8edf2;color:#4e5965}}
.basis{{margin-top:8px;color:#68717d;font-size:12px}}.muted{{color:#68717d}}.empty{{padding:20px;background:#eff9f2;border-radius:8px}}
</style></head><body><main><header><h1>Bitrix24: аудит по лучшим практикам</h1>
<p class='muted'>Снимок: {html.escape(summary.get('generated_at',''))}. Проверка выполняется только через REST API, без изменения портала.</p></header>
<section><h2>Рекомендации</h2>{"<div class='empty'>Критичных отклонений по текущему набору автоматических правил не найдено.</div>" if not finding_rows else "<table><thead><tr><th>Приоритет</th><th>Область и проблема</th><th>Факт</th><th>Риск</th><th>Что сделать</th></tr></thead><tbody>" + ''.join(finding_rows) + "</tbody></table>"}</section>
<section><h2>Покрытие REST-аудита</h2><table><thead><tr><th>Модуль</th><th>Доступно</th><th>Ошибок</th><th>Покрытие каталога</th></tr></thead><tbody>{''.join(capability_rows)}</tbody></table></section>
<section><h2>Ограничения</h2><p>Числовые пороги, помеченные как экспертная эвристика, не являются официальными лимитами Bitrix24. Следующая итерация дополняет правила ссылками на официальную документацию и проверками роботов, триггеров, прав и фактического использования бизнес-процессов.</p></section>
</main></body></html>"""


async def collect_snapshot() -> tuple[dict[str, Any], dict[str, str]]:
    collected: dict[str, Any] = {}
    errors: dict[str, str] = {}

    async def one(key: str, method: str, params: dict[str, Any] | None = None) -> None:
        try:
            collected[key] = (await bitrix_call(method, params)).get("result")
        except HTTPException as exc:
            errors[key] = str(exc.detail)

    async def many(key: str, method: str, params: dict[str, Any] | None = None, result_key: str | None = None) -> None:
        try:
            collected[key] = await bitrix_list(method, params, result_key=result_key)
        except HTTPException as exc:
            errors[key] = str(exc.detail)

    await one("profile", "profile")
    await many("users", "user.get")
    await many("departments", "department.get")
    await one("crm_deal_fields", "crm.deal.fields")
    await one("crm_contact_fields", "crm.contact.fields")
    await one("crm_company_fields", "crm.company.fields")
    await many("crm_statuses", "crm.status.list")
    await many("crm_categories", "crm.category.list", {"entityTypeId": 2}, "categories")
    await many("crm_deals", "crm.deal.list", {"select": ["ID", "CATEGORY_ID", "STAGE_ID", "ASSIGNED_BY_ID", "DATE_CREATE"]})
    await many("crm_contacts", "crm.contact.list", {"select": ["ID", "ASSIGNED_BY_ID", "DATE_CREATE"]})
    await many("crm_companies", "crm.company.list", {"select": ["ID", "ASSIGNED_BY_ID", "DATE_CREATE"]})
    await many("tasks", "tasks.task.list", {"select": ["ID", "TITLE", "STATUS", "DEADLINE", "RESPONSIBLE_ID", "GROUP_ID", "CREATED_DATE"]}, "tasks")
    await many("groups", "sonet_group.get")
    await many("disk_storages", "disk.storage.getlist")
    await many("bizproc_templates", "bizproc.workflow.template.list")
    return collected, errors


async def run_explorer_scan() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    module_stats: dict[str, dict[str, int]] = {}
    for spec in METHOD_CATALOG:
        module = spec["module"]
        module_stats.setdefault(module, {"ok": 0, "failed": 0})
        try:
            if spec["mode"] == "list":
                value = await bitrix_list(spec["method"], spec.get("params"), result_key=spec.get("result_key"), max_pages=5)
            else:
                value = (await bitrix_call(spec["method"], spec.get("params"))).get("result")
            results.append({"module": module, "method": spec["method"], "status": "ok", "count": object_count(value), "fields": sample_fields(value)})
            module_stats[module]["ok"] += 1
        except HTTPException as exc:
            results.append({"module": module, "method": spec["method"], "status": "error", "count": 0, "fields": [], "error": str(exc.detail)})
            module_stats[module]["failed"] += 1

    modules = {}
    for module, stats in module_stats.items():
        total = stats["ok"] + stats["failed"]
        modules[module] = {**stats, "coverage": round(stats["ok"] * 100 / total) if total else 0}
    return {"generated_at": datetime.now(UTC).isoformat(), "methods": results, "modules": modules}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "version": "0.3.0"}


@app.get("/api/v1/bitrix/status")
async def bitrix_status() -> dict[str, Any]:
    return {"connected": True, "profile": (await bitrix_call("profile")).get("result", {})}


@app.post("/api/v1/explorer/run")
async def explorer_run() -> dict[str, Any]:
    result = await run_explorer_scan()
    write_json(settings.reports_dir / "latest-explorer.json", result)
    return result


@app.get("/api/v1/explorer/latest")
async def explorer_latest() -> Any:
    path = settings.reports_dir / "latest-explorer.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run /api/v1/explorer/run first")
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/v1/audits/run")
async def run_audit() -> dict[str, Any]:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = settings.reports_dir / f"audit-{timestamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    collected, errors = await collect_snapshot()
    for key, value in collected.items():
        write_json(snapshot_dir / f"{key}.json", value)

    users = collected.get("users", []) if isinstance(collected.get("users"), list) else []
    departments = collected.get("departments", []) if isinstance(collected.get("departments"), list) else []
    tasks = collected.get("tasks", []) if isinstance(collected.get("tasks"), list) else []
    deals = collected.get("crm_deals", []) if isinstance(collected.get("crm_deals"), list) else []
    contacts = collected.get("crm_contacts", []) if isinstance(collected.get("crm_contacts"), list) else []
    companies = collected.get("crm_companies", []) if isinstance(collected.get("crm_companies"), list) else []
    categories = collected.get("crm_categories", []) if isinstance(collected.get("crm_categories"), list) else []
    groups = collected.get("groups", []) if isinstance(collected.get("groups"), list) else []
    bizproc = collected.get("bizproc_templates", []) if isinstance(collected.get("bizproc_templates"), list) else []

    summary = {
        "generated_at": timestamp,
        "facts": {
            "users": len(users),
            "active_users": active_users(users),
            "departments": len(departments),
            "departments_without_head": departments_without_head(departments),
            "crm_pipelines": len(categories),
            "deals": len(deals),
            "contacts": len(contacts),
            "companies": len(companies),
            "deal_custom_fields": sum(1 for key in (collected.get("crm_deal_fields") or {}) if str(key).startswith("UF_")),
            "tasks": len(tasks),
            "overdue_tasks": overdue_tasks(tasks),
            "groups": len(groups),
            "bizproc_templates": len(bizproc),
        },
        "errors": errors,
    }
    findings = create_findings(collected)
    explorer = await run_explorer_scan()

    write_json(snapshot_dir / "summary.json", summary)
    write_json(snapshot_dir / "findings.json", findings)
    write_json(snapshot_dir / "explorer.json", explorer)
    write_json(settings.reports_dir / "latest-summary.json", summary)
    write_json(settings.reports_dir / "latest-findings.json", findings)
    write_json(settings.reports_dir / "latest-explorer.json", explorer)

    report = render_advisor_report(summary, findings, explorer)
    (snapshot_dir / "report.html").write_text(report, encoding="utf-8")
    (settings.reports_dir / "latest-report.html").write_text(report, encoding="utf-8")

    return {
        "status": "completed" if not errors else "completed_with_errors",
        "snapshot": str(snapshot_dir),
        "report_url": "/api/v1/reports/latest",
        "findings": len(findings),
        "high": sum(1 for item in findings if item["severity"] == "high"),
        "medium": sum(1 for item in findings if item["severity"] == "medium"),
        "errors": errors,
    }


@app.get("/api/v1/reports/latest", response_class=HTMLResponse)
async def latest_report() -> FileResponse:
    path = settings.reports_dir / "latest-report.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No report found. Run an audit first.")
    return FileResponse(path, media_type="text/html; charset=utf-8")


@app.get("/api/v1/reports/latest/summary")
async def latest_summary() -> Any:
    path = settings.reports_dir / "latest-summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No report found. Run an audit first.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/v1/reports/latest/findings")
async def latest_findings() -> Any:
    path = settings.reports_dir / "latest-findings.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No findings found. Run an audit first.")
    return json.loads(path.read_text(encoding="utf-8"))
