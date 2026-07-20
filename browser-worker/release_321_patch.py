from __future__ import annotations

from pathlib import Path

VERSION = "3.2.1"
AUTOMATION_PATH = Path('/app/automation_dashboard.py')
VERSION_PATHS = [
    Path('/app/app.py'),
    Path('/app/admin_dashboard.py'),
    Path('/app/reference_model.py'),
    Path('/app/executive_intelligence.py'),
    Path('/app/process_optimizer.py'),
]
MARKER = 'ai-bit-automation-history-light-v321'

HISTORY_OVERRIDE = r'''
/* ai-bit-automation-history-light-v321 */
.history{padding-right:4px;scrollbar-color:#cfd3da transparent}
.event{
  background:#fff!important;
  color:#17191c!important;
  border:1px solid #e6e8ec!important;
  border-left:3px solid #d8dbe2!important;
  border-radius:10px!important;
  padding:12px 13px!important;
  margin:9px 0!important;
  box-shadow:0 1px 2px rgba(17,24,39,.035)!important;
  transition:background .15s ease,border-color .15s ease,box-shadow .15s ease;
}
.event:hover{
  background:#fafafa!important;
  border-color:#d9dce2!important;
  border-left-color:#5e6ad2!important;
  box-shadow:0 4px 14px rgba(17,24,39,.055)!important;
}
.event b,.event-head b{color:#17191c!important;font-weight:650}
.event .muted,.event .small{color:#73777f!important}
.event .bad{color:#c9364f!important}
.event .pill{
  border:1px solid #e1e4e8!important;
  background:#f4f5f7!important;
  color:#5e6269!important;
  box-shadow:none!important;
}
.event .pill.ok{
  border-color:#bfe8d5!important;
  background:#ecf8f2!important;
  color:#187653!important;
}
.event .pill.error{
  border-color:#f1c5cc!important;
  background:#fff1f3!important;
  color:#b83249!important;
}
.event .pill.running{
  border-color:#cfd3ff!important;
  background:#f0f1ff!important;
  color:#525cc7!important;
}
'''


def main() -> None:
    text = AUTOMATION_PATH.read_text(encoding='utf-8')
    if MARKER not in text:
        if '</style>' not in text:
            raise RuntimeError('automation dashboard: closing style tag not found')
        text = text.replace('</style>', HISTORY_OVERRIDE + '\n</style>', 1)
        AUTOMATION_PATH.write_text(text, encoding='utf-8')

    for path in VERSION_PATHS:
        if not path.exists():
            continue
        current = path.read_text(encoding='utf-8')
        current = current.replace('3.2.0', VERSION)
        path.write_text(current, encoding='utf-8')

    print('Applied AI-BIT Enterprise 3.2.1 — Automation History Readability Fix')


if __name__ == '__main__':
    main()
