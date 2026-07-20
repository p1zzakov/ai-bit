from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')

ROUTES = r'''

from fastapi.responses import HTMLResponse as IntegratorHTMLResponse
from integrator_diagnostics import build_integrator_diagnostics
from integrator_dashboard import integrator_dashboard_html

@app.get("/integrator", response_class=IntegratorHTMLResponse)
def integrator_page() -> IntegratorHTMLResponse:
    return IntegratorHTMLResponse(integrator_dashboard_html())

@app.get("/integrator-diagnostics/latest")
def integrator_diagnostics_latest() -> dict[str, Any]:
    return build_integrator_diagnostics(settings.browser_artifacts_dir)
'''


def main() -> None:
    app = APP.read_text(encoding='utf-8')
    if '@app.get("/integrator"' not in app:
        app += ROUTES
    app = app.replace('"version": "3.2.1"', '"version": "3.4.0"')
    APP.write_text(app, encoding='utf-8')

    admin = ADMIN.read_text(encoding='utf-8')
    if 'data-key="integrator"' not in admin:
        admin = admin.replace(
            '<button data-key="automation"><span class="icon">A</span><span class="label">Автоматизация</span></button>',
            '<button data-key="integrator"><span class="icon">T</span><span class="label">Интегратору</span></button><button data-key="automation"><span class="icon">A</span><span class="label">Автоматизация</span></button>',
            1,
        )
        admin = admin.replace(
            '<iframe class="frame" data-key="automation" data-src="/automation"></iframe>',
            '<iframe class="frame" data-key="integrator" data-src="/integrator"></iframe><iframe class="frame" data-key="automation" data-src="/automation"></iframe>',
            1,
        )
        admin = admin.replace(
            "automation:{title:'Scheduling & Automation'",
            "integrator:{title:'Интегратору',subtitle:'Технические отклонения, доказательства и план исправлений',url:'/integrator'},automation:{title:'Scheduling & Automation'",
            1,
        )
    admin = admin.replace('AI-BIT · 3.2.1', 'AI-BIT · 3.4.0').replace('AI-BIT · 3.2.0', 'AI-BIT · 3.4.0')
    ADMIN.write_text(admin, encoding='utf-8')

    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8')
        manifest = manifest.replace('VERSION = "3.2.1"', 'VERSION = "3.4.0"')
        manifest = manifest.replace('EDITION = "Automation History Readability Fix"', 'EDITION = "Integrator Technical Workbench"')
        if '"Integrator Technical Workbench"' not in manifest:
            manifest = manifest.replace('"System Health & Data Quality",', '"System Health & Data Quality",\n            "Integrator Technical Workbench",', 1)
        MANIFEST.write_text(manifest, encoding='utf-8')

    print('Applied AI-BIT Enterprise 3.4.0 — Integrator Technical Workbench')


if __name__ == '__main__':
    main()
