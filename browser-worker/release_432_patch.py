from __future__ import annotations

import re
from pathlib import Path

AUDIT = Path('/app/bitrix_onec_integration_audit.py')
APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
DASHBOARD = Path('/app/bitrix_onec_integration_dashboard.py')


def once(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return updated


def patch_audit(text: str) -> str:
    text = text.replace('VERSION = "4.3.1"', 'VERSION = "4.3.2"')
    if 'from onec_mcp_parser import build_onec_profile, decode_mcp_result' not in text:
        text = text.replace(
            'from typing import Any\n',
            'from typing import Any\n\nfrom onec_mcp_parser import build_onec_profile, decode_mcp_result\n',
            1,
        )
    text = once(
        text,
        r'def _decode_mcp_result\(value: Any\) -> Any:\n.*?\n\ndef _payload',
        'def _decode_mcp_result(value: Any) -> Any:\n    return decode_mcp_result(value)\n\n\ndef _payload',
        'replace MCP result decoder',
        re.S,
    )
    text = once(
        text,
        r'    profile = \{\n        "status": "confirmed" if configuration is not None else "insufficient_data",\n        "configuration": configuration if isinstance\(configuration, dict\) else \{\},\n        "metadata_counts": _count_named_collections\(metadata\),\n        "event_log": \{"errors": _list_size\(errors\), "warnings": _list_size\(warnings\)\},\n        "subsystems": \{"analyzed_items": _list_size\(subsystems\)\},\n    \}',
        '    profile = build_onec_profile(configuration, metadata, errors, warnings, subsystems)',
        'replace 1C profile builder',
    )
    return text


def replace_public_version(text: str) -> str:
    for old in ('4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, '4.3.2')
    return text


def main() -> None:
    AUDIT.write_text(patch_audit(AUDIT.read_text(encoding='utf-8')), encoding='utf-8')
    for path in (APP, ADMIN, MANIFEST, DASHBOARD):
        if path.exists():
            path.write_text(replace_public_version(path.read_text(encoding='utf-8')), encoding='utf-8')
    compiled = AUDIT.read_text(encoding='utf-8')
    required = ('VERSION = "4.3.2"', 'build_onec_profile(', 'decode_mcp_result(value)')
    missing = [marker for marker in required if marker not in compiled]
    if missing:
        raise RuntimeError(f'4.3.2 parser patch incomplete: {missing}')
    print('Applied AI-BIT Enterprise 4.3.2 — Resilient MCP-1C Payload Parser')


if __name__ == '__main__':
    main()
