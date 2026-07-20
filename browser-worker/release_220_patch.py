from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
VERSION_PATHS = [
    Path('/app/app.py'),
    Path('/app/admin_dashboard.py'),
    Path('/app/reference_model.py'),
    Path('/app/executive_intelligence.py'),
    Path('/app/process_optimizer.py'),
]

ROUTES = '''

from fastapi.responses import HTMLResponse as ExecutivePortalHTMLResponse
from executive_portals import (
    digital_passport_html,
    process_optimizer_html,
    ai_cio_html,
    roadmap_html,
    risk_forecast_html,
    business_value_html,
)

@app.get("/digital-passport", response_class=ExecutivePortalHTMLResponse)
def digital_passport_page() -> ExecutivePortalHTMLResponse:
    return ExecutivePortalHTMLResponse(digital_passport_html())

@app.get("/process-optimizer", response_class=ExecutivePortalHTMLResponse)
def process_optimizer_page() -> ExecutivePortalHTMLResponse:
    return ExecutivePortalHTMLResponse(process_optimizer_html())

@app.get("/ai-cio", response_class=ExecutivePortalHTMLResponse)
def ai_cio_page() -> ExecutivePortalHTMLResponse:
    return ExecutivePortalHTMLResponse(ai_cio_html())

@app.get("/transformation-roadmap", response_class=ExecutivePortalHTMLResponse)
def transformation_roadmap_page() -> ExecutivePortalHTMLResponse:
    return ExecutivePortalHTMLResponse(roadmap_html())

@app.get("/risk-forecast", response_class=ExecutivePortalHTMLResponse)
def risk_forecast_page() -> ExecutivePortalHTMLResponse:
    return ExecutivePortalHTMLResponse(risk_forecast_html())

@app.get("/business-value", response_class=ExecutivePortalHTMLResponse)
def business_value_page() -> ExecutivePortalHTMLResponse:
    return ExecutivePortalHTMLResponse(business_value_html())
'''


def main() -> None:
    # Replace the accumulated management dashboard with a stable compact implementation.
    DASH_PATH.write_text(
        "from management_compact import management_report_dashboard_html\n",
        encoding='utf-8',
    )

    app = APP_PATH.read_text(encoding='utf-8')
    if '@app.get("/digital-passport"' not in app:
        app += ROUTES
    APP_PATH.write_text(app, encoding='utf-8')

    for path in VERSION_PATHS:
        text = path.read_text(encoding='utf-8').replace('2.1.0', '2.2.0')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Enterprise 2.2.0 — Executive UX & Bitrix Digital Passport')


if __name__ == '__main__':
    main()
