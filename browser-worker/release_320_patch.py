from __future__ import annotations

from pathlib import Path

VERSION = "3.2.0"
MARKER = "ai-bit-complete-linear-ui-v320"

DASHBOARDS = [
    Path('/app/operations_dashboard.py'),
    Path('/app/business_architecture_dashboard.py'),
    Path('/app/executive_intelligence_dashboard.py'),
    Path('/app/automation_dashboard.py'),
    Path('/app/system_dashboard.py'),
    Path('/app/executive_dashboard.py'),
    Path('/app/process_dashboard.py'),
    Path('/app/reports_dashboard.py'),
    Path('/app/dashboard.py'),
]

VERSION_PATHS = [
    Path('/app/app.py'),
    Path('/app/admin_dashboard.py'),
    Path('/app/reference_model.py'),
    Path('/app/executive_intelligence.py'),
    Path('/app/process_optimizer.py'),
]

CSS = r'''
/* ai-bit-complete-linear-ui-v320 */
:root{
 color-scheme:light!important;
 --bg:#f6f7f9!important;--bg2:#fff!important;--panel:#fff!important;--panel2:#fafafa!important;
 --surface:#fff!important;--surface2:#fafafa!important;--line:#e3e5e8!important;
 --text:#191a1d!important;--muted:#6f737a!important;--accent:#5e6ad2!important;--accent2:#7866d5!important;
 --ok:#16885a!important;--warn:#ad6800!important;--bad:#c83f55!important;
}
html,body{background:#f6f7f9!important;color:#191a1d!important;-webkit-font-smoothing:antialiased}
header,.topbar,.toolbar{background:rgba(255,255,255,.96)!important;color:#191a1d!important;border-color:#e3e5e8!important;box-shadow:none!important}
main{background:#f6f7f9!important}
h1,h2,h3,h4,.title,strong,b{color:#191a1d}
p,.muted,.detail,.status,.label,small,th{color:#6f737a!important}
a{color:#525cc7!important}
.card,.section,.panel,.box,.score,.dimension,.roadmap-col,.fact,.notice,details,
.risk,.action,.rec,.feed,.roi,.dept,.road,.health,.summary,
[class*="card"],[class*="panel"]{
 background:#fff!important;color:#191a1d!important;border-color:#e3e5e8!important;
 box-shadow:0 1px 2px rgba(17,24,39,.035),0 8px 24px rgba(17,24,39,.035)!important;
}
.risk,.action,.rec{border-top:1px solid #e3e5e8!important;border-right:1px solid #e3e5e8!important;border-bottom:1px solid #e3e5e8!important}
.risk{border-left:3px solid #d75a6d!important}.action{border-left:3px solid #6570d8!important}.rec{border-left:3px solid #d69a3a!important}
.rec.high,.rec.critical{border-left-color:#d75a6d!important}
button,select,input,textarea,.button,.btn,.action-button{
 background:#fff!important;color:#303238!important;border-color:#dfe1e5!important;
 box-shadow:0 1px 2px rgba(17,24,39,.035)!important;
}
button:hover,.button:hover,.btn:hover{background:#f5f5f6!important;border-color:#cfd2d7!important}
button.primary,.button.primary,.primary,.action.primary{background:#191a1d!important;color:#fff!important;border-color:#191a1d!important}
textarea,input,select{color:#191a1d!important}
table{background:#fff!important;color:#191a1d!important}th,td{border-color:#eceef0!important}tbody tr:hover{background:#fafafa!important}
.pill,.badge{background:#f0f1f3!important;color:#555a63!important;border:1px solid #e2e4e8!important}
.badge.critical,.badge.high,.pill.critical,.pill.high{background:#fff0f2!important;color:#b83249!important;border-color:#ffd7de!important}
.badge.medium,.pill.medium{background:#fff8e8!important;color:#946000!important;border-color:#f9e7b5!important}
.bar,.progress{background:#eceef2!important}.bar span,.bar i,.progress span{background:linear-gradient(90deg,#6973dc,#8a79dc)!important}
.ring{background:conic-gradient(#6570d8 calc(var(--score)*1%),#e9eaf0 0)!important}.ring:after{background:#fff!important}
.msg,.user,.ai{background:#f7f7f8!important;color:#191a1d!important;border-color:#e3e5e8!important}
.user{background:#eef0ff!important}.notice{border-style:solid!important}
[style*="background:#0"],[style*="background: #0"],[style*="background:#1"],[style*="background: #1"],
[style*="background:linear-gradient(180deg,#0"],[style*="background: linear-gradient(180deg,#0"]{
 background:#fff!important;color:#191a1d!important;
}
[style*="color:#fff"],[style*="color: #fff"]{color:#191a1d!important}
button[style*="color:#fff"],.primary[style*="color:#fff"]{color:#fff!important}
::selection{background:#dfe2ff;color:#191a1d}
'''


def inject(path: Path) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    if MARKER not in text:
        if '</style>' not in text:
            raise RuntimeError(f'No style block in {path}')
        text = text.replace('</style>', CSS + '\n</style>', 1)
    text = text.replace('3.1.0', VERSION).replace('3.0.0', VERSION)
    path.write_text(text, encoding='utf-8')


def main() -> None:
    for path in DASHBOARDS:
        inject(path)
    for path in VERSION_PATHS:
        if path.exists():
            text = path.read_text(encoding='utf-8').replace('3.1.0', VERSION).replace('3.0.0', VERSION)
            path.write_text(text, encoding='utf-8')
    print('Applied AI-BIT Enterprise 3.2.0 — Complete Readable Linear UI Refactor')


if __name__ == '__main__':
    main()
