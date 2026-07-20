from __future__ import annotations

from pathlib import Path

VERSION = "3.1.0"
MARKER = "ai-bit-readable-linear-v31"

DASHBOARDS = [
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

VERSION_PATHS = [
    Path('/app/app.py'),
    Path('/app/admin_dashboard.py'),
    Path('/app/reference_model.py'),
    Path('/app/executive_intelligence.py'),
    Path('/app/process_optimizer.py'),
]

READABLE_OVERRIDE = r'''
/* ai-bit-readable-linear-v31 */
html{background:#f6f7f9!important}
body{background:#f6f7f9!important;color:#181a1f!important}
header,.topbar{background:rgba(255,255,255,.97)!important;color:#181a1f!important;border-color:#e4e6ea!important;box-shadow:none!important}
header h1,header h2,header h3,.topbar h1,.topbar h2,.topbar h3,h1,h2,h3,h4{color:#181a1f!important}
main{background:#f6f7f9!important}
a{color:#525cc7!important}
.card,.section,.panel,.box,details,.notice,.health,.tile,.stat,.widget{background:#fff!important;color:#181a1f!important;border-color:#e4e6ea!important;box-shadow:0 1px 2px rgba(17,24,39,.035),0 8px 24px rgba(17,24,39,.035)!important}
.card:hover,.section:hover{border-color:#d7d9df!important}
.metric,.value,.score,strong,b{color:#202228}
.muted,.status,.label,small,p,.note,.description{color:#70747c!important}
.risk,.action,.msg,.user,.ai,.decision,.optimizer-card,.optimizer-rec{background:#fff!important;color:#202228!important;border:1px solid #e6e8ec!important;border-left-width:3px!important;box-shadow:none!important}
.risk{border-left-color:#d84a5f!important}
.action,.decision{border-left-color:#5e6ad2!important}
.risk p,.action p,.msg p,.decision p{color:#70747c!important}
.user{background:#f1f2ff!important;border-color:#dfe1ff!important;margin-left:12%!important}
.ai{background:#fafafa!important;border-color:#e6e8ec!important}
textarea,input,select{background:#fff!important;color:#181a1f!important;border-color:#dfe1e6!important;box-shadow:inset 0 1px 1px rgba(17,24,39,.02)!important}
textarea:focus,input:focus,select:focus{outline:2px solid rgba(94,106,210,.17)!important;border-color:#9ca3e8!important}
button,.btn,.action-button{background:#fff!important;color:#34373d!important;border-color:#dfe1e6!important;box-shadow:0 1px 2px rgba(17,24,39,.035)!important}
button:hover,.btn:hover{background:#f7f7f8!important;border-color:#cfd2d8!important}
button.primary,.primary,.action.primary{background:#202124!important;color:#fff!important;border-color:#202124!important}
.quick button{background:#f8f8fa!important;color:#4f566b!important}
.bar{background:#eceef2!important}
.bar i{background:#5e6ad2!important}
.ok{color:#16845a!important}.warn{color:#a9650d!important}.bad{color:#c83f55!important}.accent{color:#525cc7!important}
table{background:#fff!important;color:#202228!important}
th{background:#fafafa!important;color:#555961!important}
th,td,.row{border-color:#eceef1!important}
code,pre{background:#f5f6f8!important;color:#24272d!important;border-color:#e4e6ea!important}
[style*="background:#121f34"],[style*="background: #121f34"],[style*="background:#0d192a"],[style*="background:#172640"]{background:#fff!important;color:#202228!important}
'''


def inject(path: Path) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    if MARKER in text or '</style>' not in text:
        return
    text = text.replace('</style>', READABLE_OVERRIDE + '\n</style>', 1)
    path.write_text(text, encoding='utf-8')


def main() -> None:
    for path in DASHBOARDS:
        inject(path)

    for path in VERSION_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8').replace('3.0.0', VERSION)
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Enterprise 3.1.0 — Readable Linear Design System')


if __name__ == '__main__':
    main()
