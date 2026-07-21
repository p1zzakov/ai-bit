from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
AUDIT = Path('/app/bitrix_onec_integration_audit.py')
SOURCE = Path('/app/source_provider.py')


def patch_source(text: str) -> str:
    if 'from integration_verification_pipeline import augment_onec_calls' not in text:
        text = text.replace(
            'from typing import Any\n',
            'from typing import Any\n\nfrom integration_verification_pipeline import augment_onec_calls\n',
            1,
        )
    anchor = '        self.calls = [row for row in calls if isinstance(row, dict)]'
    replacement = anchor + '\n        self.calls = augment_onec_calls(self.provider_id, self.allowed_tools, self.calls)'
    if replacement not in text:
        if anchor not in text:
            raise RuntimeError('McpProvider calls anchor not found')
        text = text.replace(anchor, replacement, 1)
    for old in ('VERSION = "4.3.3"', 'VERSION = "4.3.2"', 'VERSION = "4.3.1"', 'VERSION = "4.3.0"'):
        text = text.replace(old, 'VERSION = "4.4.0"')
    return text


def patch_audit(text: str) -> str:
    if 'from integration_verification_pipeline import DISCOVERY_CALLS, build_verification_pipeline' not in text:
        marker = 'from typing import Any\n'
        text = text.replace(
            marker,
            marker + '\nfrom integration_verification_pipeline import DISCOVERY_CALLS, build_verification_pipeline\n',
            1,
        )
    for old in ('VERSION = "4.3.3"', 'VERSION = "4.3.2"', 'VERSION = "4.3.1"'):
        text = text.replace(old, 'VERSION = "4.4.0"')
    anchor = '    onec = _latest_onec(root)\n'
    addition = anchor + '    verification_pipeline = build_verification_pipeline(bitrix, onec)\n'
    if addition not in text:
        if anchor not in text:
            raise RuntimeError('audit onec anchor not found')
        text = text.replace(anchor, addition, 1)
    payload_anchor = '        "source_evidence": source_evidence,\n'
    payload_addition = payload_anchor + '        "verification_pipeline": verification_pipeline,\n'
    if payload_addition not in text:
        if payload_anchor not in text:
            raise RuntimeError('audit payload anchor not found')
        text = text.replace(payload_anchor, payload_addition, 1)
    text = text.replace(
        '        "required_mcp_calls": _required_calls(),',
        '        "required_mcp_calls": [*_required_calls(), *DISCOVERY_CALLS, *verification_pipeline.get("verification_calls", [])],',
        1,
    )
    text = text.replace(
        '    overall = "ready_for_mapping" if source_confirmed == len(source_evidence) else "attention" if source_confirmed else "insufficient_data"',
        '    overall = verification_pipeline.get("status") if source_confirmed == len(source_evidence) else "attention" if source_confirmed else "insufficient_data"',
        1,
    )
    return text


def replace_public_version(text: str) -> str:
    for old in ('4.3.3', '4.3.2', '4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, '4.4.0')
    return text


def main() -> None:
    SOURCE.write_text(patch_source(SOURCE.read_text(encoding='utf-8')), encoding='utf-8')
    AUDIT.write_text(patch_audit(AUDIT.read_text(encoding='utf-8')), encoding='utf-8')
    for path in (APP, ADMIN, MANIFEST):
        if path.exists():
            path.write_text(replace_public_version(path.read_text(encoding='utf-8')), encoding='utf-8')
    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8')
        for edition in (
            'EDITION = "MCP-1C Markdown Payload Parser"',
            'EDITION = "Confirmed Bitrix24 ↔ 1C Evidence"',
            'EDITION = "Bitrix24 ↔ 1C Integration Audit"',
        ):
            manifest = manifest.replace(edition, 'EDITION = "Integration Verification Pipeline"')
        MANIFEST.write_text(manifest, encoding='utf-8')
    required = {
        SOURCE: ('augment_onec_calls(', 'VERSION = "4.4.0"'),
        AUDIT: ('build_verification_pipeline(bitrix, onec)', '"verification_pipeline": verification_pipeline', 'VERSION = "4.4.0"'),
    }
    for path, markers in required.items():
        compiled = path.read_text(encoding='utf-8')
        missing = [marker for marker in markers if marker not in compiled]
        if missing:
            raise RuntimeError(f'4.4.0 patch incomplete for {path.name}: {missing}')
    print('Applied AI-BIT Enterprise 4.4.0 — Integration Verification Pipeline')


if __name__ == '__main__':
    main()
