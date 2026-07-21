from __future__ import annotations

import re
from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
SOURCE_PROVIDER = Path('/app/source_provider.py')
TARGET_VERSION = '4.3.1'


def replace_versions(text: str) -> str:
    # Update known release markers left by earlier patches.
    for old in ('4.3.0', '3.6.1', '3.6.0', '3.5.1', '3.5.0', '3.4.2', '3.4.0', '3.2.1'):
        text = text.replace(old, TARGET_VERSION)

    # Harden the public metadata version even when an older patch introduced
    # an unexpected semantic version literal.
    text = re.sub(
        r'(["\']version["\']\s*:\s*["\'])\d+\.\d+\.\d+(["\'])',
        rf'\g<1>{TARGET_VERSION}\2',
        text,
    )
    text = re.sub(
        r'(FastAPI\([^\n]*?version\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
        rf'\g<1>{TARGET_VERSION}\2',
        text,
    )
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

    # Fail the image build if the public version was not actually updated.
    if APP.exists() and TARGET_VERSION not in APP.read_text(encoding='utf-8'):
        raise RuntimeError('AI-BIT 4.3.1 version marker was not applied to app.py')

    print('Applied AI-BIT Enterprise 4.3.1 — Confirmed Bitrix24 ↔ 1C Evidence')


if __name__ == '__main__':
    main()
