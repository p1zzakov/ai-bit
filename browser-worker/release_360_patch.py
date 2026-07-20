from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')

ROUTES = r'''

from fastapi.responses import HTMLResponse as ExternalSourcesHTMLResponse
from external_sources_dashboard import external_sources_dashboard_html
from source_provider import (
    collect_external_sources,
    external_sources_status,
    latest_external_sources,
)

@app.get("/external-sources", response_class=ExternalSourcesHTMLResponse)
def external_sources_page() -> ExternalSourcesHTMLResponse:
    return ExternalSourcesHTMLResponse(external_sources_dashboard_html())

@app.get("/external-sources/status")
def external_sources_status_route() -> dict[str, Any]:
    return external_sources_status()

@app.get("/external-sources/latest")
def external_sources_latest_route() -> dict[str, Any]:
    return latest_external_sources(settings.browser_artifacts_dir)

@app.post("/external-sources/collect")
def external_sources_collect_route() -> dict[str, Any]:
    return collect_external_sources(settings.browser_artifacts_dir)
'''


def main() -> None:
    app = APP.read_text(encoding='utf-8')
    if '@app.get("/external-sources"' not in app:
        app += ROUTES
    for old in ('"version": "3.5.1"', '"version": "3.5.0"', '"version": "3.4.2"'):
        app = app.replace(old, '"version": "3.6.0"')
    APP.write_text(app, encoding='utf-8')

    if ADMIN.exists():
        admin = ADMIN.read_text(encoding='utf-8')
        anchor = "integrator:{icon:'T',label:'Аудит интегратора'"
        if 'externalSources:{' not in admin and anchor in admin:
            admin = admin.replace(
                anchor,
                "externalSources:{icon:'D',label:'Источники данных',title:'External Data Sources',subtitle:'1С HTTP, MCP и единый evidence-слой',url:'/external-sources'},\n " + anchor,
                1,
            )
        admin = admin.replace('AI-BIT · 3.5.1', 'AI-BIT · 3.6.0').replace('AI-BIT · 3.5.0', 'AI-BIT · 3.6.0')
        ADMIN.write_text(admin, encoding='utf-8')

    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8')
        for old in ('VERSION = "3.5.1"', 'VERSION = "3.5.0"', 'VERSION = "3.4.2"'):
            manifest = manifest.replace(old, 'VERSION = "3.6.0"')
        manifest = manifest.replace('EDITION = "Read-Only Implementation Blueprint"', 'EDITION = "External Source Providers"')
        MANIFEST.write_text(manifest, encoding='utf-8')

    print('Applied AI-BIT Enterprise 3.6.0 — External Source Providers')


if __name__ == '__main__':
    main()
