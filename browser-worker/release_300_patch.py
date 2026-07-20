from __future__ import annotations

from pathlib import Path

VERSION = "3.0.0"
MARKER = "ai-bit-linear-design-system-v3"

ADMIN_PATH = Path('/app/admin_dashboard.py')
VERSION_PATHS = [
    Path('/app/app.py'),
    Path('/app/admin_dashboard.py'),
    Path('/app/reference_model.py'),
    Path('/app/executive_intelligence.py'),
    Path('/app/process_optimizer.py'),
]

LEGACY_DASHBOARDS = [
    Path('/app/dashboard.py'),
    Path('/app/operations_dashboard.py'),
    Path('/app/executive_dashboard.py'),
    Path('/app/process_dashboard.py'),
    Path('/app/business_architecture_dashboard.py'),
    Path('/app/reports_dashboard.py'),
    Path('/app/automation_dashboard.py'),
    Path('/app/system_dashboard.py'),
    Path('/app/executive_intelligence_dashboard.py'),
]

ADMIN_OVERRIDE = r'''
/* ai-bit-linear-design-system-v3 */
:root{color-scheme:light;--bg:#f7f8fa;--bg2:#ffffff;--sidebar:#fbfbfc;--surface:#ffffff;--surface2:#f8f8fa;--line:#e6e8ec;--text:#17191c;--muted:#73777f;--accent:#5e6ad2;--accent2:#7c68d9;--ok:#1f9d68;--warn:#c47a13;--bad:#d84a5f;--shadow:0 1px 2px rgba(17,24,39,.04),0 12px 32px rgba(17,24,39,.055)}
body{color:var(--text);background:var(--bg);-webkit-font-smoothing:antialiased}.shell{grid-template-columns:224px minmax(0,1fr)}.sidebar{padding:18px 12px;border-right:1px solid var(--line);background:var(--sidebar);backdrop-filter:none}.brand{padding:2px 8px 19px}.logo{width:36px;height:36px;border-radius:10px;font-size:14px;background:linear-gradient(135deg,#5e6ad2,#7c68d9);box-shadow:none}.brand h1{color:var(--text);font-size:14px;letter-spacing:-.01em}.brand p{color:var(--muted);font-size:10px}.section-label{color:#9a9da4;padding:9px 10px 6px;font-size:9px;letter-spacing:1.2px}.nav{gap:2px}.nav button{color:#676b72;padding:8px 9px;border-radius:7px;gap:9px}.nav button:hover{color:var(--text);background:#f0f1f3;transform:none}.nav button.active{color:var(--text);background:#ededf0;border-color:transparent;box-shadow:none}.icon{width:24px;height:24px;border-radius:6px;background:#eff0f2;color:#73777f;font-size:11px}.nav button.active .icon{background:#dfe1ff;color:#525cc7}.health{border-color:var(--line);border-radius:10px;background:#fff}.version{color:#a2a5ab}.workspace{grid-template-rows:64px minmax(0,1fr)}.topbar{padding:0 20px;border-bottom:1px solid var(--line);background:rgba(255,255,255,.9);backdrop-filter:blur(10px)}.page-title h2{font-size:16px;color:var(--text);letter-spacing:-.015em}.page-title p{color:var(--muted)}.action{border-color:var(--line);background:#fff;color:#555961;padding:8px 10px;border-radius:8px;box-shadow:0 1px 2px rgba(17,24,39,.03)}.action:hover{border-color:#d3d6dc;color:var(--text);background:#f8f8f9}.action.primary{background:#17191c;border-color:#17191c;color:#fff;box-shadow:none}.content{padding:14px}.viewport{border-color:var(--line);border-radius:12px;background:#fff;box-shadow:var(--shadow)}.frame{background:#f7f8fa}.loader{background:rgba(247,248,250,.76)}.spinner{border-color:#d9dce2;border-top-color:var(--accent)}
'''

LEGACY_OVERRIDE = r'''
/* ai-bit-linear-design-system-v3 */
:root{color-scheme:light!important;--bg:#f7f8fa!important;--bg2:#ffffff!important;--panel:#ffffff!important;--panel2:#fbfbfc!important;--surface:#ffffff!important;--surface2:#fbfbfc!important;--line:#e6e8ec!important;--text:#17191c!important;--muted:#73777f!important;--accent:#5e6ad2!important;--accent2:#7c68d9!important;--ok:#1f9d68!important;--warn:#c47a13!important;--bad:#d84a5f!important;--shadow:0 1px 2px rgba(17,24,39,.04),0 10px 28px rgba(17,24,39,.05)!important}body{background:#f7f8fa!important;color:#17191c!important;-webkit-font-smoothing:antialiased}.card,.section,.panel,.box,details{background:#fff!important;border-color:#e6e8ec!important;box-shadow:0 1px 2px rgba(17,24,39,.025)!important}.topbar,header{border-color:#e6e8ec!important}.btn,button,.action{border-color:#e6e8ec!important;background:#fff!important;color:#42464d!important;box-shadow:0 1px 2px rgba(17,24,39,.03)!important}.primary,.action.primary{background:#17191c!important;border-color:#17191c!important;color:#fff!important}.muted,.status,.label,small,p{color:#73777f}.row{border-color:#eff0f2!important}
'''


def inject_style(path: Path, css: str) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    if MARKER in text or '</style>' not in text:
        return
    text = text.replace('</style>', css + '\n</style>', 1)
    path.write_text(text, encoding='utf-8')


def main() -> None:
    inject_style(ADMIN_PATH, ADMIN_OVERRIDE)
    for path in LEGACY_DASHBOARDS:
        inject_style(path, LEGACY_OVERRIDE)

    # Embedded frames always receive an explicit mode marker. New executive
    # portal links use target=_top, preventing nested Unified Admin layouts.
    admin = ADMIN_PATH.read_text(encoding='utf-8')
    admin = admin.replace('data-src="/executive"', 'data-src="/executive?embedded=1"')
    admin = admin.replace('data-src="/dashboard"', 'data-src="/dashboard?embedded=1"')
    admin = admin.replace('data-src="/operations"', 'data-src="/operations?embedded=1"')
    admin = admin.replace('data-src="/processes"', 'data-src="/processes?embedded=1"')
    admin = admin.replace('data-src="/business-architecture"', 'data-src="/business-architecture?embedded=1"')
    admin = admin.replace('data-src="/reports-ui"', 'data-src="/reports-ui?embedded=1"')
    admin = admin.replace('data-src="/automation"', 'data-src="/automation?embedded=1"')
    admin = admin.replace('data-src="/system"', 'data-src="/system?embedded=1"')
    admin = admin.replace("AI-BIT · 2.2.0", f"AI-BIT · {VERSION}")
    admin = admin.replace("AI-BIT · 1.0.0-rc.6", f"AI-BIT · {VERSION}")
    ADMIN_PATH.write_text(admin, encoding='utf-8')

    for path in VERSION_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8').replace('2.2.0', VERSION)
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Enterprise 3.0.0 — Linear Design System & Unified Layout')


if __name__ == '__main__':
    main()
