from __future__ import annotations

import re
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


def ensure_integrator_workspace(admin: str) -> str:
    """Repair every Integrator workspace component independently."""
    button_marker = '<button data-key="integrator"'
    iframe_markup = '<iframe class="frame" data-key="integrator" data-src="/integrator"></iframe>'
    iframe_marker = 'data-key="integrator" data-src="/integrator"'
    meta_marker = "integrator:{title:'Интегратору'"

    if button_marker not in admin:
        automation_button = '<button data-key="automation"><span class="icon">A</span><span class="label">Автоматизация</span></button>'
        admin = admin.replace(
            automation_button,
            '<button data-key="integrator"><span class="icon">T</span><span class="label">Интегратору</span></button>' + automation_button,
            1,
        )

    if iframe_marker not in admin:
        automation_iframe = '<iframe class="frame" data-key="automation" data-src="/automation"></iframe>'
        if automation_iframe in admin:
            admin = admin.replace(automation_iframe, iframe_markup + automation_iframe, 1)
        else:
            # Later release patches may change the iframe order or surrounding markup.
            # Inject before the viewport closes instead of silently leaving a partial workspace.
            pattern = r'(</div></main></section></div><script>)'
            admin, count = re.subn(pattern, iframe_markup + r'\1', admin, count=1)
            if count != 1:
                raise RuntimeError('Unable to locate dashboard viewport for Integrator iframe')

    if meta_marker not in admin:
        automation_meta = "automation:{title:'Scheduling & Automation'"
        if automation_meta not in admin:
            raise RuntimeError('Unable to locate automation metadata for Integrator workspace')
        admin = admin.replace(
            automation_meta,
            "integrator:{title:'Интегратору',subtitle:'Технические отклонения, доказательства и план исправлений',url:'/integrator'}," + automation_meta,
            1,
        )

    unsafe = "button.classList.add('active');frame.classList.add('active');$('#title').textContent=meta[key].title;$('#subtitle').textContent=meta[key].subtitle;if(!frame.src)"
    safe = "if(!button||!frame){console.error('AI-BIT workspace is incomplete',key,{button,frame});return}button.classList.add('active');frame.classList.add('active');$('#title').textContent=meta[key].title;$('#subtitle').textContent=meta[key].subtitle;if(!frame.src)"
    if unsafe in admin:
        admin = admin.replace(unsafe, safe, 1)

    required = (button_marker, iframe_marker, meta_marker)
    missing = [marker for marker in required if marker not in admin]
    if missing:
        raise RuntimeError(f'Integrator workspace patch incomplete: {missing}')

    return admin


def main() -> None:
    app = APP.read_text(encoding='utf-8')
    if '@app.get("/integrator"' not in app:
        app += ROUTES
    app = app.replace('"version": "3.2.1"', '"version": "3.4.0"')
    APP.write_text(app, encoding='utf-8')

    admin = ensure_integrator_workspace(ADMIN.read_text(encoding='utf-8'))
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
