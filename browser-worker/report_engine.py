from __future__ import annotations

import json
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from branding import DEVELOPER_EMAIL, DEVELOPER_NAME, inject_attribution


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _latest_crawl(artifacts_dir: Path) -> dict[str, Any] | None:
    root = artifacts_dir / "history"
    files = sorted(root.glob("*.json"), reverse=True)
    for path in files:
        data = _read_json(path)
        if data:
            return data
    return None


def _latest(artifacts_dir: Path, folder: str) -> dict[str, Any] | None:
    return _read_json(artifacts_dir / folder / "latest.json")


def _metric(label: str, value: Any, suffix: str = "") -> str:
    return f'<div class="metric"><span>{escape(label)}</span><strong>{escape(str(value if value is not None else "—"))}{escape(suffix)}</strong></div>'


def _recommendation_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<div class="empty">Критичных рекомендаций не выявлено.</div>'
    return "".join(
        f'<article class="recommendation"><div class="severity">{escape(str(row.get("severity", "info")))}</div>'
        f'<h3>{escape(str(row.get("title", "Рекомендация")))}</h3>'
        f'<p>{escape(str(row.get("finding", "")))}</p>'
        f'<p><b>Действие:</b> {escape(str(row.get("action", "")))}</p></article>'
        for row in rows[:30]
    )


def build_report_payload(artifacts_dir: Path) -> dict[str, Any]:
    crawl = _latest_crawl(artifacts_dir) or {}
    operations = _latest(artifacts_dir, "operations") or {}
    architecture = _latest(artifacts_dir, "business-architecture") or {}
    process_mining = _latest(artifacts_dir, "process-mining") or {}

    assessment = crawl.get("assessment") or {}
    deep_audit = crawl.get("deep_audit") or {}
    recommendations: list[dict[str, Any]] = []
    recommendations.extend(operations.get("recommendations") or [])
    recommendations.extend(architecture.get("recommendations") or [])
    recommendations.extend(deep_audit.get("action_plan") or [])

    return {
        "version": "1.0.0-rc.7",
        "generated_at": datetime.now(UTC).isoformat(),
        "developer": {"name": DEVELOPER_NAME, "email": DEVELOPER_EMAIL},
        "executive": {
            "enterprise_health": architecture.get("enterprise_health"),
            "implementation_score": assessment.get("implementation_score"),
            "open_tasks": (operations.get("summary") or {}).get("open"),
            "overdue_tasks": (operations.get("summary") or {}).get("overdue"),
            "overdue_rate": (operations.get("summary") or {}).get("overdue_rate"),
            "without_deadline": (operations.get("summary") or {}).get("without_deadline"),
            "employees_at_risk": (operations.get("summary") or {}).get("employees_at_risk"),
        },
        "implementation": assessment,
        "deep_audit": deep_audit,
        "operations": operations,
        "process_mining": process_mining,
        "business_architecture": architecture,
        "recommendations": recommendations,
        "plan": {
            "30_days": [r for r in recommendations if str(r.get("severity", "")).lower() in {"critical", "high"}][:10],
            "60_days": [r for r in recommendations if str(r.get("severity", "")).lower() == "medium"][:10],
            "90_days": [r for r in recommendations if str(r.get("severity", "")).lower() not in {"critical", "high", "medium"}][:10],
        },
    }


def render_report_html(payload: dict[str, Any]) -> str:
    ex = payload.get("executive") or {}
    arch = payload.get("business_architecture") or {}
    domains = arch.get("domains") or {}
    pm = payload.get("process_mining") or {}
    pms = pm.get("summary") or {}
    generated = escape(str(payload.get("generated_at", "")))
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>AI-BIT Enterprise Report</title><style>
@page{{size:A4;margin:14mm}}*{{box-sizing:border-box}}body{{font:13px/1.5 Arial,sans-serif;color:#172033;margin:0;background:#fff}}header{{padding:24px 0;border-bottom:3px solid #5b7cfa;margin-bottom:22px}}h1{{font-size:28px;margin:0}}h2{{margin:28px 0 12px;font-size:20px}}h3{{margin:0 0 6px}}.muted{{color:#65718a}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}.metric{{border:1px solid #dce3f0;border-radius:10px;padding:12px;background:#f7f9fd}}.metric span{{display:block;color:#65718a;font-size:11px}}.metric strong{{font-size:23px}}.section{{break-inside:avoid;margin-bottom:18px}}.recommendation{{border-left:4px solid #f0a23a;background:#fff8ec;padding:12px;margin:9px 0;border-radius:6px}}.severity{{font-size:10px;text-transform:uppercase;color:#a15f00}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #dce3f0;text-align:left}}.empty{{padding:16px;background:#f7f9fd;border-radius:8px}}footer{{margin-top:30px;border-top:1px solid #dce3f0;padding-top:10px;color:#65718a;font-size:10px}}
</style></head><body><header><h1>AI-BIT Enterprise</h1><div class="muted">Управленческий отчёт по аудиту Bitrix24 · {generated}</div></header>
<section class="section"><h2>Executive Summary</h2><div class="grid">
{_metric("Enterprise Health", ex.get("enterprise_health"), "%")}{_metric("Зрелость внедрения", ex.get("implementation_score"), "%")}{_metric("Открытые задачи", ex.get("open_tasks"))}{_metric("Просрочено", ex.get("overdue_tasks"))}{_metric("Доля просрочки", ex.get("overdue_rate"), "%")}{_metric("Без срока", ex.get("without_deadline"))}{_metric("Сотрудники в риске", ex.get("employees_at_risk"))}{_metric("Кандидаты на автоматизацию", pms.get("automation_candidates"))}
</div></section>
<section class="section"><h2>Бизнес-архитектура</h2><table><thead><tr><th>Контур</th><th>Оценка</th><th>Статус</th><th>Evidence</th></tr></thead><tbody>
{''.join(f'<tr><td>{escape(str(k))}</td><td>{escape(str(v.get("score", "—")))}%</td><td>{escape(str(v.get("status", "—")))}</td><td>{escape(str(v.get("evidence_status", "—")))}</td></tr>' for k,v in domains.items())}
</tbody></table></section>
<section class="section"><h2>Process Mining</h2><div class="grid">{_metric("Проанализировано задач", pms.get("tasks_analyzed"))}{_metric("Повторяющиеся паттерны", pms.get("repeated_patterns"))}{_metric("Узкие места", pms.get("potential_bottlenecks"))}{_metric("Ручные часы", pms.get("estimated_manual_hours"))}</div></section>
<section><h2>Ключевые рекомендации</h2>{_recommendation_rows(payload.get("recommendations") or [])}</section>
<section><h2>План 30 / 60 / 90 дней</h2><h3>30 дней</h3>{_recommendation_rows((payload.get("plan") or {}).get("30_days") or [])}<h3>60 дней</h3>{_recommendation_rows((payload.get("plan") or {}).get("60_days") or [])}<h3>90 дней</h3>{_recommendation_rows((payload.get("plan") or {}).get("90_days") or [])}</section>
<footer>AI-BIT Enterprise · Разработчик: {escape(DEVELOPER_NAME)} · {escape(DEVELOPER_EMAIL)} · read-only audit</footer></body></html>'''


async def generate_report(artifacts_dir: Path) -> dict[str, Any]:
    payload = build_report_payload(artifacts_dir)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = artifacts_dir / "reports"
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"executive-report-{stamp}.json"
    html_path = root / f"executive-report-{stamp}.html"
    pdf_path = root / f"executive-report-{stamp}.pdf"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html = inject_attribution(render_report_html(payload))
    html_path.write_text(html, encoding="utf-8")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(path=str(pdf_path), format="A4", print_background=True)
        await browser.close()
    manifest = {
        "id": stamp,
        "generated_at": payload["generated_at"],
        "json": str(json_path),
        "html": str(html_path),
        "pdf": str(pdf_path),
        "summary": payload.get("executive", {}),
        "developer": payload.get("developer", {}),
    }
    (root / "latest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def list_reports(artifacts_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    root = artifacts_dir / "reports"
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("executive-report-*.json"), reverse=True)[:limit]:
        data = _read_json(path) or {}
        stamp = path.stem.replace("executive-report-", "")
        rows.append({"id": stamp, "generated_at": data.get("generated_at"), "summary": data.get("executive", {})})
    return rows


def report_file(artifacts_dir: Path, report_id: str, fmt: str) -> Path:
    if fmt not in {"json", "html", "pdf"}:
        raise ValueError("format must be json, html or pdf")
    path = artifacts_dir / "reports" / f"executive-report-{report_id}.{fmt}"
    if not path.exists():
        raise FileNotFoundError(report_id)
    return path
