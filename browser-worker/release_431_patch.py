from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
SOURCE_PROVIDER = Path('/app/source_provider.py')


def replace_versions(text: str) -> str:
    for old in ('4.3.0', '3.6.1', '3.6.0'):
        text = text.replace(old, '4.3.1')
    return text


def main() -> None:
    for path in (APP, ADMIN, MANIFEST, SOURCE_PROVIDER):
        if path.exists():
            path.write_text(replace_versions(path.read_text(encoding='utf-8')), encoding='utf-8')

    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8')
        for edition in (
            'EDITION = "Bitrix24 ↔ 1C Integration Audit"',
            'EDITION = "Universal MCP Provider Framework"',
            'EDITION = "External Source Providers"',
        ):
            manifest = manifest.replace(edition, 'EDITION = "Confirmed Bitrix24 ↔ 1C Evidence"')
        MANIFEST.write_text(manifest, encoding='utf-8')

    print('Applied AI-BIT Enterprise 4.3.1 — Confirmed Bitrix24 ↔ 1C Evidence')


if __name__ == '__main__':
    main()
