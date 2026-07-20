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
    app = app.replace('1.0.0-rc.10', '1.0.0-rc.11')
    app = once(
        app,
        'from management_report_dashboard import management_report_dashboard_html',
        'from management_report_dashboard import management_report_dashboard_html\nfrom executive_intelligence import build_executive_intelligence, read_latest_executive_intelligence\nfrom executive_intelligence_dashboard import executive_intelligence_dashboard_html',
        'executive intelligence imports',
    )
    marker = '''@app.get("/management-report", response_class=HTMLResponse)
async def management_report_ui() -> str:
    return management_report_dashboard_html()
'''
    addition = marker + '''

@app.get("/executive-intelligence", response_class=HTMLResponse)
async def executive_intelligence_ui() -> str:
    return executive_intelligence_dashboard_html()


@app.post("/executive-intelligence/collect")
async def executive_intelligence_collect() -> dict[str, Any]:
    return build_executive_intelligence(settings.browser_artifacts_dir)


@app.get("/executive-intelligence/latest")
async def executive_intelligence_latest() -> dict[str, Any]:
    try:
        return read_latest_executive_intelligence(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return build_executive_intelligence(settings.browser_artifacts_dir)
'''
    app = once(app, marker, addition, 'executive intelligence endpoints')
    APP_PATH.write_text(app, encoding='utf-8')

    admin = ADMIN_PATH.read_text(encoding='utf-8')
    admin = admin.replace('1.0.0-rc.10', '1.0.0-rc.11')
    management_button = '<button data-key="management"><span class="icon">M</span><span class="label">Отчёт для руководства</span></button>'
    admin = once(admin, management_button, management_button + '<button data-key="intelligence"><span class="icon">X</span><span class="label">Executive Intelligence</span></button>', 'intelligence nav')
    management_frame = '<iframe class="frame" data-key="management" data-src="/management-report?embedded=1"></iframe>'
    admin = once(admin, management_frame, management_frame + '<iframe class="frame" data-key="intelligence" data-src="/executive-intelligence?embedded=1"></iframe>', 'intelligence frame')
    management_meta = "management:{title:'Отчёт для руководства',subtitle:'Понятное заключение без технического жаргона',url:'/management-report'}"
    admin = once(admin, management_meta, management_meta + ",intelligence:{title:'Executive Intelligence Suite',subtitle:'Цифровая зрелость, риски, ROI и дорожная карта',url:'/executive-intelligence'}", 'intelligence meta')
    ADMIN_PATH.write_text(admin, encoding='utf-8')
    print('Applied AI-BIT Executive Intelligence Suite patch 1.0.0-rc.11')


if __name__ == '__main__':
    main()
