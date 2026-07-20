from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')


def replace(path: Path, pairs: tuple[tuple[str, str], ...]) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')


def main() -> None:
    replace(
        APP,
        (
            ('"version": "3.4.2"', '"version": "3.5.0"'),
            ('"version": "3.4.1"', '"version": "3.5.0"'),
            ('"version": "3.4.0"', '"version": "3.5.0"'),
        ),
    )
    replace(
        MANIFEST,
        (
            ('VERSION = "3.4.2"', 'VERSION = "3.5.0"'),
            ('VERSION = "3.4.1"', 'VERSION = "3.5.0"'),
            ('VERSION = "3.4.0"', 'VERSION = "3.5.0"'),
        ),
    )
    replace(
        ADMIN,
        (
            ('AI-BIT · 3.4.2', 'AI-BIT · 3.5.0'),
            ("label:'Интегратору',title:'Для интегратора',subtitle:'Технические отклонения, доказательства и план исправлений'", "label:'Аудит интегратора',title:'Bitrix24 Engineering Audit',subtitle:'Объекты, REST, evidence и технический TODO'"),
        ),
    )
    print('Applied AI-BIT Enterprise 3.5.0 — Bitrix24 Engineering Audit')


if __name__ == '__main__':
    main()
