from __future__ import annotations

import shutil
from pathlib import Path

SOURCE_PATH = Path('/app/management_brief_dashboard_v2.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
VERSION_PATHS = [
    Path('/app/app.py'),
    Path('/app/admin_dashboard.py'),
    Path('/app/executive_intelligence.py'),
    Path('/app/reference_model.py'),
]


def main() -> None:
    if not SOURCE_PATH.exists():
        raise RuntimeError('management brief v2 source is missing')
    shutil.copyfile(SOURCE_PATH, DASH_PATH)
    for path in VERSION_PATHS:
        text = path.read_text(encoding='utf-8')
        text = text.replace('2.0.0-alpha.5', '2.0.0-alpha.6')
        path.write_text(text, encoding='utf-8')
    print('Applied AI-BIT Resilient Executive Brief 2.0.0-alpha.6')


if __name__ == '__main__':
    main()
