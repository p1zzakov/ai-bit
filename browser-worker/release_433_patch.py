from __future__ import annotations

from pathlib import Path

AUDIT = Path('/app/bitrix_onec_integration_audit.py')
APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
DASHBOARD = Path('/app/bitrix_onec_integration_dashboard.py')
PARSER = Path('/app/onec_mcp_parser.py')


def replace_public_version(text: str) -> str:
    for old in ('4.3.2', '4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, '4.3.3')
    return text


def main() -> None:
    for path in (AUDIT, APP, ADMIN, MANIFEST, DASHBOARD):
        if path.exists():
            path.write_text(replace_public_version(path.read_text(encoding='utf-8')), encoding='utf-8')

    parser = PARSER.read_text(encoding='utf-8')
    required = (
        'PARSER_VERSION = "4.3.3"',
        '_markdown_metadata_counts',
        '"transport_confirmed"',
        '"payload_decoded"',
        '"raw_format"',
    )
    missing = [marker for marker in required if marker not in parser]
    if missing:
        raise RuntimeError(f'4.3.3 parser patch incomplete: {missing}')

    audit = AUDIT.read_text(encoding='utf-8')
    if 'VERSION = "4.3.3"' not in audit:
        raise RuntimeError('4.3.3 public audit version was not applied')

    print('Applied AI-BIT Enterprise 4.3.3 — MCP-1C Markdown Payload Parser')


if __name__ == '__main__':
    main()
