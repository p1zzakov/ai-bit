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
    replace(APP, (( '"version": "3.6.0"', '"version": "3.6.1"'),))
    replace(MANIFEST, (( 'VERSION = "3.6.0"', 'VERSION = "3.6.1"'),))
    replace(
        ADMIN,
        (
            ('AI-BIT · 3.6.0', 'AI-BIT · 3.6.1'),
            ("label:'Источники данных',title:'External Data Sources',subtitle:'1С HTTP, MCP и единый evidence-формат'", "label:'Источники данных',title:'Enterprise MCP Sources',subtitle:'Универсальные MCP-серверы, allowlist и read-only evidence'"),
        ),
    )
    print('Applied AI-BIT Enterprise 3.6.1 — Universal MCP Provider Framework')


if __name__ == '__main__':
    main()
