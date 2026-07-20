from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def main() -> None:
    for path in (APP_PATH, ADMIN_PATH):
        text = path.read_text(encoding='utf-8')
        for version in ('1.0.0-rc.11', '1.0.0-rc.12', '1.0.0-rc.13'):
            text = text.replace(version, '1.0.0-rc.14')
        path.write_text(text, encoding='utf-8')
    print('Applied AI-BIT Executive Brief patch 1.0.0-rc.14')


if __name__ == '__main__':
    main()
