from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    app = APP_PATH.read_text(encoding='utf-8')
    app = app.replace('1.0.0-rc.9', '1.0.0-rc.10')
    app = once(
        app,
        'from reports_dashboard import reports_dashboard_html',
        'from reports_dashboard import reports_dashboard_html\nfrom management_report import generate_management_report, list_management_reports, management_report_file\nfrom management_report_dashboard import management_report_dashboard_html',
        'management report imports',
    )
    marker = '''@app.get("/reports-ui", response_class=HTMLResponse)
async def reports_ui() -> str:
    return reports_dashboard_html()
'''
    addition = marker + '''

@app.get("/management-report", response_class=HTMLResponse)
async def management_report_ui() -> str:
    return management_report_dashboard_html()


@app.get("/management-reports")
async def management_reports_list(limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    return list_management_reports(settings.browser_artifacts_dir, limit=limit)


@app.post("/management-reports/generate")
async def management_reports_generate(mode: str = Query(default="short", pattern="^(short|detailed)$")) -> dict[str, Any]:
    try:
        return await generate_management_report(settings.browser_artifacts_dir, mode=mode)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/management-reports/{report_id}/{fmt}")
async def management_reports_download(report_id: str, fmt: str):
    try:
        path = management_report_file(settings.browser_artifacts_dir, report_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Management report not found") from None
    media = {"json": "application/json", "html": "text/html; charset=utf-8", "pdf": "application/pdf"}[fmt]
    return FileResponse(path, media_type=media, filename=path.name)
'''
    app = once(app, marker, addition, 'management report endpoints')
    APP_PATH.write_text(app, encoding='utf-8')

    admin = ADMIN_PATH.read_text(encoding='utf-8')
    admin = admin.replace('1.0.0-rc.9', '1.0.0-rc.10')
    reports_button = '<button data-key="reports"><span class="icon">R</span><span class="label">Отчёты</span></button>'
    admin = once(admin, reports_button, reports_button + '<button data-key="management"><span class="icon">M</span><span class="label">Отчёт для руководства</span></button>', 'management nav')
    reports_frame = '<iframe class="frame" data-key="reports" data-src="/reports-ui?embedded=1"></iframe>'
    admin = once(admin, reports_frame, reports_frame + '<iframe class="frame" data-key="management" data-src="/management-report?embedded=1"></iframe>', 'management frame')
    reports_meta = "reports:{title:'Reports & Export',subtitle:'Управленческие отчёты HTML, JSON и PDF',url:'/reports-ui'}"
    admin = once(admin, reports_meta, reports_meta + ",management:{title:'Отчёт для руководства',subtitle:'Понятное заключение без технического жаргона',url:'/management-report'}", 'management meta')
    ADMIN_PATH.write_text(admin, encoding='utf-8')
    print('Applied AI-BIT Management Report patch 1.0.0-rc.10')


if __name__ == '__main__':
    main()
