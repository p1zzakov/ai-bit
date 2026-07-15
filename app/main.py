from __future__ import annotations

import html
import json
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
app = FastAPI(title=settings.app_name, version="0.2.0")


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


async def bitrix_call(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.bitrix_webhook_url:
        raise HTTPException(status_code=503, detail="BITRIX_WEBHOOK_URL is not configured")

    url = f"{settings.bitrix_webhook_url.rstrip('/')}/{method}.json"
    try:
        async with httpx.AsyncClient(
            timeout=settings.bitrix_request_timeout,
            verify=settings.bitrix_verify_tls,
        ) as client:
            response = await client.post(url, json=params or {})
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Bitrix24 request failed: {exc}") from exc

    if "error" in payload:
        description = payload.get("error_description", "")
        raise HTTPException(
            status_code=502,
            detail=f"Bitrix24 API error: {payload['error']}: {description}",
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
    """Read a paginated Bitrix24 list without modifying the portal."""
    items: list[Any] = []
    start: int | str = 0
    base_params = dict(params or {})

    for _ in range(max_pages):
        request_params = {**base_params, "start": start}
        payload = await bitrix_call(method, request_params)
        items.extend(extract_items(payload.get("result"), result_key))

        next_value = payload.get("next")
        if next_value is None:
            break
        start = next_value

    return items


def field_count(fields: Any) -> int:
    return len(fields) if isinstance(fields, dict) else 0


def active_users(users: list[Any]) -> int:
    return sum(1 for user in users if str(user.get("ACTIVE", "Y")).upper() == "Y")


def departments_without_head(departments: list[Any]) -> int:
    return sum(1 for department in departments if not department.get("UF_HEAD"))


def overdue_tasks(tasks: list[Any]) -> int:
    now = datetime.now(UTC)
    count = 0
    for task in tasks:
        deadline = task.get("deadline") or task.get("DEADLINE")
        status = str(task.get("status") or task.get("STATUS") or "")
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


def section_status(available: bool, count: int | None = None) -> tuple[str, str]:
    if not available:
        return "Требует проверки", "gray"
    if count is not None and count == 0:
        return "Не настроено или не используется", "red"
    return "Обнаружено и используется", "green"


def render_report(summary: dict[str, Any], errors: dict[str, str]) -> str:
    generated = html.escape(summary["generated_at"])
    sections = summary["sections"]

    rows: list[str] = []
    for title, section in sections.items():
        status, color = section_status(section["available"], section.get("primary_count"))
        facts = "<br>".join(
            f"<b>{html.escape(str(key))}:</b> {html.escape(str(value))}"
            for key, value in section["facts"].items()
        )
        note = html.escape(section.get("note", ""))
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(title)}</strong></td>"
            f"<td><span class='badge {color}'>{html.escape(status)}</span></td>"
            f"<td>{facts}</td>"
            f"<td>{note}</td>"
            "</tr>"
        )

    error_block = ""
    if errors:
        error_rows = "".join(
            f"<li><b>{html.escape(key)}</b>: {html.escape(value)}</li>"
            for key, value in errors.items()
        )
        error_block = f"<section><h2>Что API не позволил проверить</h2><ul>{error_rows}</ul></section>"

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ревизия внедрения Битрикс24</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f4f6f8;color:#20242a}}
main{{max-width:1200px;margin:32px auto;padding:0 20px}}
header,section{{background:white;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 2px 10px #00000010}}
h1{{margin:0 0 8px}} .muted{{color:#68717d}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:14px;border-bottom:1px solid #e5e8eb;text-align:left;vertical-align:top}}
th{{background:#f8fafb}} .badge{{display:inline-block;padding:6px 10px;border-radius:999px;font-size:13px;font-weight:bold}}
.green{{background:#dcf7e7;color:#176b3a}} .red{{background:#ffe1e1;color:#962929}} .gray{{background:#e8edf2;color:#4e5965}}
.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:18px}}
.card{{background:#f8fafb;padding:16px;border-radius:10px}} .card b{{font-size:26px;display:block}}
</style>
</head>
<body><main>
<header>
<h1>Ревизия внедрения Битрикс24</h1>
<div class="muted">Сформировано: {generated}. Отчёт основан на фактических данных REST API и не изменяет портал.</div>
<div class="summary">
<div class="card"><b>{summary['headline']['active_users']}</b>активных пользователей</div>
<div class="card"><b>{summary['headline']['departments']}</b>подразделений</div>
<div class="card"><b>{summary['headline']['deals']}</b>сделок</div>
<div class="card"><b>{summary['headline']['tasks']}</b>задач</div>
</div>
</header>
<section>
<h2>Фактическое состояние</h2>
<table><thead><tr><th>Блок</th><th>Предварительный статус</th><th>Что найдено</th><th>Комментарий</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</section>
{error_block}
<section><h2>Как читать отчёт</h2><p>Зелёный статус означает, что сущности обнаружены и используются. Красный — сущности не найдены. Серый — раздел нельзя достоверно оценить через выданные права REST API и требуется ручная проверка интерфейса или документации интегратора.</p></section>
</main></body></html>"""


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/v1/bitrix/status")
async def bitrix_status() -> dict[str, Any]:
    result = await bitrix_call("profile")
    return {"connected": True, "profile": result.get("result", {})}


@app.post("/api/v1/audits/run")
async def run_audit() -> dict[str, Any]:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = settings.reports_dir / f"audit-{timestamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    collected: dict[str, Any] = {}
    errors: dict[str, str] = {}

    async def collect_one(key: str, method: str, params: dict[str, Any] | None = None) -> None:
        try:
            collected[key] = (await bitrix_call(method, params)).get("result")
        except HTTPException as exc:
            errors[key] = str(exc.detail)

    async def collect_list(
        key: str,
        method: str,
        params: dict[str, Any] | None = None,
        result_key: str | None = None,
    ) -> None:
        try:
            collected[key] = await bitrix_list(method, params, result_key=result_key)
        except HTTPException as exc:
            errors[key] = str(exc.detail)

    await collect_one("profile", "profile")
    await collect_list("users", "user.get")
    await collect_list("departments", "department.get")

    await collect_one("crm_deal_fields", "crm.deal.fields")
    await collect_one("crm_contact_fields", "crm.contact.fields")
    await collect_one("crm_company_fields", "crm.company.fields")
    await collect_list("crm_statuses", "crm.status.list")
    await collect_list("crm_categories", "crm.category.list", {"entityTypeId": 2}, "categories")
    await collect_list("crm_deals", "crm.deal.list", {"select": ["ID", "CATEGORY_ID", "STAGE_ID", "ASSIGNED_BY_ID", "DATE_CREATE"]})
    await collect_list("crm_contacts", "crm.contact.list", {"select": ["ID", "ASSIGNED_BY_ID", "DATE_CREATE"]})
    await collect_list("crm_companies", "crm.company.list", {"select": ["ID", "ASSIGNED_BY_ID", "DATE_CREATE"]})

    await collect_list(
        "tasks",
        "tasks.task.list",
        {"select": ["ID", "TITLE", "STATUS", "DEADLINE", "RESPONSIBLE_ID", "GROUP_ID", "CREATED_DATE"]},
        "tasks",
    )
    await collect_list("groups", "sonet_group.get")
    await collect_list("disk_storages", "disk.storage.getlist")
    await collect_list("bizproc_templates", "bizproc.workflow.template.list")

    for key, value in collected.items():
        write_json(snapshot_dir / f"{key}.json", value)

    users = collected.get("users", []) if isinstance(collected.get("users"), list) else []
    departments = collected.get("departments", []) if isinstance(collected.get("departments"), list) else []
    deals = collected.get("crm_deals", []) if isinstance(collected.get("crm_deals"), list) else []
    contacts = collected.get("crm_contacts", []) if isinstance(collected.get("crm_contacts"), list) else []
    companies = collected.get("crm_companies", []) if isinstance(collected.get("crm_companies"), list) else []
    categories = collected.get("crm_categories", []) if isinstance(collected.get("crm_categories"), list) else []
    statuses = collected.get("crm_statuses", []) if isinstance(collected.get("crm_statuses"), list) else []
    tasks = collected.get("tasks", []) if isinstance(collected.get("tasks"), list) else []
    groups = collected.get("groups", []) if isinstance(collected.get("groups"), list) else []
    storages = collected.get("disk_storages", []) if isinstance(collected.get("disk_storages"), list) else []
    bizproc = collected.get("bizproc_templates", []) if isinstance(collected.get("bizproc_templates"), list) else []

    summary = {
        "generated_at": timestamp,
        "headline": {
            "active_users": active_users(users),
            "departments": len(departments),
            "deals": len(deals),
            "tasks": len(tasks),
        },
        "sections": {
            "Структура компании": {
                "available": "users" in collected and "departments" in collected,
                "primary_count": len(departments),
                "facts": {
                    "Пользователей всего": len(users),
                    "Активных пользователей": active_users(users),
                    "Подразделений": len(departments),
                    "Подразделений без руководителя": departments_without_head(departments),
                },
                "note": "Наличие данных подтверждено. Корректность оргструктуры нужно сверить с утверждённой структурой компании.",
            },
            "CRM": {
                "available": "crm_deals" in collected,
                "primary_count": len(deals),
                "facts": {
                    "Воронок сделок": len(categories),
                    "CRM-статусов и стадий": len(statuses),
                    "Сделок": len(deals),
                    "Контактов": len(contacts),
                    "Компаний": len(companies),
                    "Пользовательских полей сделок": field_count(collected.get("crm_deal_fields")),
                },
                "note": "Факт использования CRM виден по данным. Соответствие воронок бизнес-процессам и настройку роботов проверим отдельным этапом.",
            },
            "Задачи и проекты": {
                "available": "tasks" in collected,
                "primary_count": len(tasks),
                "facts": {
                    "Задач": len(tasks),
                    "Просроченных незавершённых": overdue_tasks(tasks),
                    "Рабочих групп и проектов": len(groups),
                },
                "note": "Использование подтверждено при наличии задач. Шаблоны, регламенты постановки и качество исполнения требуют отдельной оценки.",
            },
            "Бизнес-процессы": {
                "available": "bizproc_templates" in collected,
                "primary_count": len(bizproc),
                "facts": {"Шаблонов бизнес-процессов": len(bizproc)},
                "note": "REST показывает доступные шаблоны, но не всегда раскрывает роботов, ошибки выполнения и фактическое покрытие процессов.",
            },
            "Диск и документы": {
                "available": "disk_storages" in collected,
                "primary_count": len(storages),
                "facts": {"Хранилищ Диска": len(storages)},
                "note": "Наличие хранилищ не подтверждает завершённость документооборота. Нужна ручная проверка маршрутов согласования и шаблонов документов.",
            },
        },
        "errors": errors,
    }

    summary_path = snapshot_dir / "summary.json"
    report_path = snapshot_dir / "report.html"
    write_json(summary_path, summary)
    report_path.write_text(render_report(summary, errors), encoding="utf-8")

    latest_summary = settings.reports_dir / "latest-summary.json"
    latest_report = settings.reports_dir / "latest-report.html"
    write_json(latest_summary, summary)
    latest_report.write_text(render_report(summary, errors), encoding="utf-8")

    return {
        "status": "completed" if not errors else "completed_with_errors",
        "snapshot": str(snapshot_dir),
        "summary": str(summary_path),
        "report": str(report_path),
        "report_url": "/api/v1/reports/latest",
        "sections_collected": list(collected),
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
