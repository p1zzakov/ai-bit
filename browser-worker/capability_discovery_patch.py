from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
REF_PATH = Path('/app/reference_model.py')
EXEC_PATH = Path('/app/executive_intelligence.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    ref = REF_PATH.read_text(encoding='utf-8')
    ref = ref.replace('VERSION = "2.0.0-alpha.1"', 'VERSION = "2.0.0-alpha.2"')
    ref = once(
        ref,
        'from typing import Any\n',
        'from typing import Any\n\nfrom capability_discovery import discover_capabilities\n',
        'capability discovery import',
    )
    ref = once(
        ref,
        '    reference = load_reference_model(profile)\n    operations = _read(artifacts_dir / "operations" / "latest.json")',
        '    reference = load_reference_model(profile)\n    discovery = discover_capabilities(artifacts_dir)\n    discovered = discovery.get("capabilities") or {}\n    operations = _read(artifacts_dir / "operations" / "latest.json")',
        'discovery collection',
    )
    ref = once(
        ref,
        '        status = str(item.get("forced_status") or "").strip().lower()\n        evidence_found: list[str] = []\n        if not status:',
        '''        forced = str(item.get("forced_status") or "").strip().lower()
        detected = discovered.get(str(item.get("id"))) or {}
        status = forced
        evidence_found: list[str] = []
        source = "forced" if forced else "reference_evidence"
        confidence = 1.0 if forced else 0.0
        if not status and detected.get("status") in {"implemented", "partial"}:
            status = str(detected.get("status"))
            evidence_found.extend(detected.get("evidence") or [])
            source = "automatic_discovery"
            confidence = float(detected.get("confidence") or 0)
        if not status:''',
        'discovered capability resolution',
    )
    ref = once(
        ref,
        '            if evidence_found:\n                status = "implemented"\n            else:\n                status = "unknown"',
        '            if evidence_found:\n                status = "implemented"\n                confidence = max(confidence, 0.85)\n            else:\n                status = "unknown"\n                confidence = max(confidence, 0.2)',
        'evidence confidence',
    )
    ref = once(
        ref,
        '            "status": status,\n            "evidence": evidence_found,',
        '            "status": status,\n            "evidence": evidence_found,\n            "source": source,\n            "confidence": round(confidence, 2),',
        'capability source metadata',
    )
    ref = once(
        ref,
        '        "requires_verification": unknown[:15],\n    }',
        '        "requires_verification": unknown[:15],\n        "automatic_discovery": discovery.get("summary", {}),\n    }',
        'discovery summary result',
    )
    REF_PATH.write_text(ref, encoding='utf-8')

    app = APP_PATH.read_text(encoding='utf-8')
    app = once(
        app,
        'from reference_model import build_reference_audit, load_reference_model, read_latest_reference_audit',
        'from reference_model import build_reference_audit, load_reference_model, read_latest_reference_audit\nfrom capability_discovery import discover_capabilities, read_latest_capability_discovery',
        'app discovery imports',
    )
    marker = '''@app.post("/reference-audit/collect")
async def reference_audit_collect() -> dict[str, Any]:
    return build_reference_audit(settings.browser_artifacts_dir)
'''
    addition = marker + '''

@app.post("/capability-discovery/collect")
async def capability_discovery_collect() -> dict[str, Any]:
    return discover_capabilities(settings.browser_artifacts_dir)


@app.get("/capability-discovery/latest")
async def capability_discovery_latest() -> dict[str, Any]:
    try:
        return read_latest_capability_discovery(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return discover_capabilities(settings.browser_artifacts_dir)
'''
    app = once(app, marker, addition, 'capability discovery endpoints')
    app = app.replace('2.0.0-alpha.1', '2.0.0-alpha.2')
    APP_PATH.write_text(app, encoding='utf-8')

    for path in (EXEC_PATH, ADMIN_PATH):
        text = path.read_text(encoding='utf-8')
        text = text.replace('2.0.0-alpha.1', '2.0.0-alpha.2')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Automatic Capability Discovery 2.0.0-alpha.2')


if __name__ == '__main__':
    main()
