from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from groq import Groq
from playwright.async_api import async_playwright

VERSION = "1.0.0-rc.10"


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _latest_crawl(root: Path) -> dict[str, Any]:
    for path in sorted((root / "history").glob("*.json"), reverse=True):
        data = _read(path)
        if data:
            return data
    return {}


def build_management_context(root: Path) -> dict[str, Any]:
    crawl = _latest_crawl(root)
    operations = _read(root / "operations" / "latest.json")
    architecture = _read(root / "business-architecture" / "latest.json")
    mining = _read(root / "process-mining" / "latest.json")
    assessment = crawl.get("assessment") or {}
    deep = crawl.get("deep_audit") or {}
    return {
        "implementation": {
            "score": assessment.get("implementation_score"),
            "counts": assessment.get("counts", {}),
            "recommendations": assessment.get("recommendations", [])[:20],
        },
        "operations": {
            "summary": operations.get("summary", {}),
            "recommendations": operations.get("recommendations", [])[:20],
            "departments_at_risk": [x for x in operations.get("departments", []) if x.get("risk") in {"high", "critical"}][:15],
        },
        "business_architecture": {
            "enterprise_health": architecture.get("enterprise_health"),
            "summary": architecture.get("summary", {}),
            "domains": {
                key: {
                    "score": value.get("score"),
                    "status": value.get("status"),
                    "summary": value.get("summary", {}),
                    "recommendations": value.get("recommendations", [])[:12],
                }
                for key, value in (architecture.get("domains") or {}).items()
            },
            "recommendations": architecture.get("recommendations", [])[:25],
        },
        "process_mining": {
            "summary": mining.get("summary", {}),
            "automation_candidates": mining.get("automation_candidates", [])[:15],
            "bottlenecks": mining.get("bottlenecks", [])[:10],
        },
        "deep_audit": {
            "summary": deep.get("summary", {}),
            "action_plan": deep.get("action_plan", [])[:20],
        },
    }


def _prompt(mode: str) -> str:
    length = "краткий отчёт объёмом примерно 1–2 страницы" if mode == "short" else "подробный отчёт по всем направлениям"
    return f"""Ты готовишь {length} для генерального директора компании о качестве внедрения Bitrix24.
Пиши простым деловым русским языком без технических терминов, названий API, REST, webhook, crawl, JSON и программного жаргона.
Не выдумывай факты. Если данных недостаточно, прямо напиши об этом. Цифры используй только когда они помогают руководителю понять масштаб проблемы.
Не оценивай личности сотрудников. Оценивай организацию работы, контроль, нагрузку, процессы и качество управления.
Верни строго JSON со структурой:
{{
  "title": "Отчёт для руководства",
  "overall_assessment": "связное общее заключение",
  "strengths": ["что работает хорошо"],
  "weaknesses": ["основные слабые места"],
  "sections": {{
    "administration": {{"assessment":"...","recommendations":["..."]}},
    "task_management": {{"assessment":"...","recommendations":["..."]}},
    "business_processes": {{"assessment":"...","recommendations":["..."]}},
    "sales_crm": {{"assessment":"...","recommendations":["..."]}},
    "document_flow": {{"assessment":"...","recommendations":["..."]}},
    "automation": {{"assessment":"...","recommendations":["..."]}}
  }},
  "main_risks": ["риск и его последствие"],
  "top_priorities": ["конкретное действие в порядке приоритета"],
  "plan": {{"30_days":["..."],"60_days":["..."],"90_days":["..."]}},
  "conclusion": "итоговое заключение для руководства"
}}
Каждый вывод должен быть понятен человеку без IT-подготовки и опираться на переданные данные."""


def _render_list(items: list[Any]) -> str:
    if not items:
        return '<p class="muted">Значимых пунктов не выявлено.</p>'
    return "<ul>" + "".join(f"<li>{escape(str(x))}</li>" for x in items) + "</ul>"


def render_html(report: dict[str, Any]) -> str:
    sections = report.get("sections") or {}
    titles = {
        "administration": "Администрирование и управление системой",
        "task_management": "Организация работы и контроль задач",
        "business_processes": "Бизнес-процессы",
        "sales_crm": "Продажи и работа с клиентами",
        "document_flow": "Документооборот",
        "automation": "Автоматизация",
    }
    section_html = "".join(
        f'<section><h2>{escape(titles[key])}</h2><p>{escape(str((sections.get(key) or {}).get("assessment", "Данных недостаточно.")))}</p>'
        f'<h3>Что рекомендуется</h3>{_render_list((sections.get(key) or {}).get("recommendations", []))}</section>'
        for key in titles
    )
    plan = report.get("plan") or {}
    generated = escape(str(report.get("generated_at", "")))
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Отчёт для руководства</title><style>
@page{{size:A4;margin:16mm}}*{{box-sizing:border-box}}body{{max-width:980px;margin:auto;padding:36px;font:15px/1.65 Arial,sans-serif;color:#172033;background:#fff}}header{{border-bottom:4px solid #5876e8;padding-bottom:20px;margin-bottom:26px}}h1{{font-size:30px;margin:0 0 6px}}h2{{font-size:21px;margin-top:30px;color:#22335b}}h3{{font-size:15px;margin-bottom:4px}}section{{break-inside:avoid;border-bottom:1px solid #e5e9f1;padding-bottom:16px}}.lead{{font-size:17px;background:#f4f7ff;border-left:5px solid #5876e8;padding:18px;border-radius:8px}}.muted{{color:#68758c}}li{{margin:6px 0}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.card{{padding:16px;border:1px solid #dce3f0;border-radius:10px;background:#f8faff}}footer{{margin-top:32px;padding-top:12px;border-top:1px solid #dce3f0;color:#68758c;font-size:11px}}@media(max-width:700px){{body{{padding:20px}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>{escape(str(report.get("title", "Отчёт для руководства")))}</h1><div class="muted">Сформирован {generated}</div></header>
<section><h2>Общая оценка</h2><div class="lead">{escape(str(report.get("overall_assessment", "")))}</div></section>
<div class="grid"><section class="card"><h2>Что работает хорошо</h2>{_render_list(report.get("strengths", []))}</section><section class="card"><h2>Основные слабые места</h2>{_render_list(report.get("weaknesses", []))}</section></div>
{section_html}
<section><h2>Главные риски</h2>{_render_list(report.get("main_risks", []))}</section>
<section><h2>Что сделать в первую очередь</h2>{_render_list(report.get("top_priorities", []))}</section>
<section><h2>План на 30 / 60 / 90 дней</h2><h3>Ближайшие 30 дней</h3>{_render_list(plan.get("30_days", []))}<h3>В течение 60 дней</h3>{_render_list(plan.get("60_days", []))}<h3>В течение 90 дней</h3>{_render_list(plan.get("90_days", []))}</section>
<section><h2>Итог для руководства</h2><div class="lead">{escape(str(report.get("conclusion", "")))}</div></section>
<footer>AI-BIT Enterprise · Разработчик: Коваленко А.С. · pizzakov@gmail.com</footer></body></html>'''


async def generate_management_report(root: Path, mode: str = "short") -> dict[str, Any]:
    if mode not in {"short", "detailed"}:
        raise ValueError("mode must be short or detailed")
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile").strip()
    context = build_management_context(root)
    client = Groq(api_key=key, timeout=120.0)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.15,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _prompt(mode)},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
    )
    content = completion.choices[0].message.content or "{}"
    report = json.loads(content)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    generated_at = datetime.now(UTC).isoformat()
    report.update({"id": stamp, "version": VERSION, "mode": mode, "generated_at": generated_at, "provider": "groq", "model": model})
    folder = root / "management-reports"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"management-report-{stamp}.json"
    html_path = folder / f"management-report-{stamp}.html"
    pdf_path = folder / f"management-report-{stamp}.pdf"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html = render_html(report)
    html_path.write_text(html, encoding="utf-8")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(path=str(pdf_path), format="A4", print_background=True)
        await browser.close()
    manifest = {"id": stamp, "generated_at": generated_at, "mode": mode, "json": str(json_path), "html": str(html_path), "pdf": str(pdf_path), "title": report.get("title")}
    (folder / "latest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def list_management_reports(root: Path, limit: int = 50) -> list[dict[str, Any]]:
    folder = root / "management-reports"
    rows = []
    for path in sorted(folder.glob("management-report-*.json"), reverse=True)[:limit]:
        data = _read(path)
        if data:
            rows.append({"id": data.get("id", path.stem.removeprefix("management-report-")), "generated_at": data.get("generated_at"), "mode": data.get("mode"), "title": data.get("title")})
    return rows


def management_report_file(root: Path, report_id: str, fmt: str) -> Path:
    if fmt not in {"json", "html", "pdf"}:
        raise ValueError("format must be json, html or pdf")
    if not report_id.replace("T", "").replace("Z", "").isdigit():
        raise ValueError("invalid report id")
    path = root / "management-reports" / f"management-report-{report_id}.{fmt}"
    if not path.exists():
        raise FileNotFoundError(path)
    return path
