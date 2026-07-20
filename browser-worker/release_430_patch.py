from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
SOURCE_PROVIDER = Path('/app/source_provider.py')

ROUTES = r'''

from fastapi.responses import HTMLResponse as BitrixOneCIntegrationHTMLResponse
from bitrix_onec_integration_audit import build_integration_audit, latest_integration_audit
from bitrix_onec_integration_dashboard import bitrix_onec_integration_dashboard_html

@app.get("/bitrix-onec-integration", response_class=BitrixOneCIntegrationHTMLResponse)
def bitrix_onec_integration_page() -> BitrixOneCIntegrationHTMLResponse:
    return BitrixOneCIntegrationHTMLResponse(bitrix_onec_integration_dashboard_html())

@app.get("/bitrix-onec-integration/latest")
def bitrix_onec_integration_latest() -> dict[str, Any]:
    return latest_integration_audit(settings.browser_artifacts_dir)

@app.post("/bitrix-onec-integration/collect")
def bitrix_onec_integration_collect() -> dict[str, Any]:
    collect_external_sources(settings.browser_artifacts_dir)
    return build_integration_audit(settings.browser_artifacts_dir)
'''


def main() -> None:
    app = APP.read_text(encoding='utf-8')
    if '@app.get("/bitrix-onec-integration"' not in app:
        app += ROUTES
    for old in ('"version": "3.6.1"', '"version": "3.6.0"', '"version": "3.5.1"'):
        app = app.replace(old, '"version": "4.3.0"')
    APP.write_text(app, encoding='utf-8')

    if SOURCE_PROVIDER.exists():
        source = SOURCE_PROVIDER.read_text(encoding='utf-8')
        source = source.replace('VERSION = "3.6.1"', 'VERSION = "4.3.0"')
        source = source.replace(
            '            started = time.monotonic()\n            response = client.request("tools/call", {"name": name, "arguments": arguments})',
            '            call_id = str(row.get("id") or name)\n            annotations = discovered[name].get("annotations") if isinstance(discovered[name], dict) else {}\n            if not isinstance(annotations, dict) or annotations.get("readOnlyHint") is not True:\n                errors.append({"tool": name, "id": call_id, "error": "tool_not_declared_read_only"})\n                continue\n            started = time.monotonic()\n            response = client.request("tools/call", {"name": name, "arguments": arguments})',
        )
        source = source.replace(
            '            calls_result[name] = {\n                "success": not bool(response.get("error")),',
            '            calls_result[call_id] = {\n                "tool": name,\n                "success": not bool(response.get("error")),',
        )
        SOURCE_PROVIDER.write_text(source, encoding='utf-8')

    if ADMIN.exists():
        admin = ADMIN.read_text(encoding='utf-8')
        anchor = "externalSources:{icon:'D',label:'Источники данных'"
        if 'bitrixOneC:{' not in admin and anchor in admin:
            admin = admin.replace(
                anchor,
                "bitrixOneC:{icon:'1C',label:'Bitrix ↔ 1С',title:'Bitrix24 ↔ 1С Integration Audit',subtitle:'Топология, данные, синхронизация и Blueprint',url:'/bitrix-onec-integration'},\n " + anchor,
                1,
            )
        for old in ('AI-BIT · 3.6.1', 'AI-BIT · 3.6.0', 'AI-BIT · 3.5.1'):
            admin = admin.replace(old, 'AI-BIT · 4.3.0')
        ADMIN.write_text(admin, encoding='utf-8')

    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8')
        for old in ('VERSION = "3.6.1"', 'VERSION = "3.6.0"', 'VERSION = "3.5.1"'):
            manifest = manifest.replace(old, 'VERSION = "4.3.0"')
        for edition in ('EDITION = "Universal MCP Provider Framework"', 'EDITION = "External Source Providers"'):
            manifest = manifest.replace(edition, 'EDITION = "Bitrix24 ↔ 1C Integration Audit"')
        MANIFEST.write_text(manifest, encoding='utf-8')

    print('Applied AI-BIT Enterprise 4.3.0 — Bitrix24 ↔ 1C Integration Audit')


if __name__ == '__main__':
    main()
