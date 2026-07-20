from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
REF_PATH = Path('/app/reference_model.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
EXEC_PATH = Path('/app/executive_intelligence.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    ref = REF_PATH.read_text(encoding='utf-8')
    ref = ref.replace('VERSION = "2.0.0-alpha.2"', 'VERSION = "2.0.0-alpha.3"')
    ref = once(
        ref,
        'from capability_discovery import discover_capabilities\n',
        'from capability_discovery import discover_capabilities\nfrom evidence_engine import build_evidence_audit\n',
        'evidence engine import',
    )
    ref = once(
        ref,
        '    discovery = discover_capabilities(artifacts_dir)\n    discovered = discovery.get("capabilities") or {}\n',
        '    discovery = discover_capabilities(artifacts_dir)\n    discovered = discovery.get("capabilities") or {}\n    evidence_audit = build_evidence_audit(artifacts_dir)\n    evidence_matrix = evidence_audit.get("capabilities") or {}\n',
        'evidence audit collection',
    )
    ref = once(
        ref,
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
        '''        capability_id = str(item.get("id"))
        detected = discovered.get(capability_id) or {}
        evidence_result = evidence_matrix.get(capability_id) or {}
        status = str(evidence_result.get("status") or "")
        evidence_found: list[str] = []
        source = "evidence_audit" if status else "reference_evidence"
        confidence = float(evidence_result.get("confidence") or 0)
        for checked in evidence_result.get("checked_sources") or []:
            evidence_found.extend(checked.get("evidence") or [])
        if not status and detected.get("status") in {"implemented", "partial"}:
            status = str(detected.get("status"))
            evidence_found.extend(detected.get("evidence") or [])
            source = "automatic_discovery"
            confidence = float(detected.get("confidence") or 0)
        if not status:''',
        'evidence-first capability resolution',
    )
    ref = once(
        ref,
        '            "confidence": round(confidence, 2),\n',
        '            "confidence": round(confidence, 2),\n            "evidence_audit": evidence_result,\n',
        'evidence matrix in capability result',
    )
    ref = once(
        ref,
        '        "automatic_discovery": discovery.get("summary", {}),\n',
        '        "automatic_discovery": discovery.get("summary", {}),\n        "evidence_audit": {"summary": evidence_audit.get("summary", {}), "methodology": evidence_audit.get("methodology", {})},\n',
        'evidence audit summary',
    )
    REF_PATH.write_text(ref, encoding='utf-8')

    app = APP_PATH.read_text(encoding='utf-8')
    app = once(
        app,
        'from capability_discovery import discover_capabilities, read_latest_capability_discovery',
        'from capability_discovery import discover_capabilities, read_latest_capability_discovery\nfrom evidence_engine import build_evidence_audit, read_latest_evidence_audit',
        'app evidence imports',
    )
    marker = '''@app.get("/capability-discovery/latest")
async def capability_discovery_latest() -> dict[str, Any]:
    try:
        return read_latest_capability_discovery(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return discover_capabilities(settings.browser_artifacts_dir)
'''
    addition = marker + '''

@app.post("/evidence-audit/collect")
async def evidence_audit_collect() -> dict[str, Any]:
    return build_evidence_audit(settings.browser_artifacts_dir)


@app.get("/evidence-audit/latest")
async def evidence_audit_latest() -> dict[str, Any]:
    try:
        return read_latest_evidence_audit(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return build_evidence_audit(settings.browser_artifacts_dir)
'''
    app = once(app, marker, addition, 'evidence audit endpoints')
    app = app.replace('2.0.0-alpha.2', '2.0.0-alpha.3')
    APP_PATH.write_text(app, encoding='utf-8')

    dash = DASH_PATH.read_text(encoding='utf-8')
    old = "<p><b class=\"bad\">Не реализовано</b> · '+esc(x.domain||'')+'</p></div></div>'"
    new = "<p><b class=\"bad\">'+(x.status==='missing'?'Не найдено подтверждений':esc(x.status||'Требует проверки'))+'</b> · '+esc(x.domain||'')+' · уверенность '+Math.round(Number(x.confidence||0)*100)+'%</p><details><summary>Показать доказательства</summary><p>'+esc(((x.evidence_audit||{}).rationale)||'Обоснование отсутствует.')+'</p>'+(((x.evidence_audit||{}).checked_sources||[]).map(s=>'<div class=\"decision\"><b>'+esc(s.title||s.id)+'</b><span>'+(s.available?(s.positive?'Найдено подтверждение':'Проверено, подтверждений не найдено'):'Источник недоступен')+'</span></div>').join(''))+'</details></div></div>'"
    if old not in dash:
        raise RuntimeError('dashboard evidence details marker not found')
    dash = dash.replace(old, new, 1)
    DASH_PATH.write_text(dash, encoding='utf-8')

    for path in (EXEC_PATH, ADMIN_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.2', '2.0.0-alpha.3')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Evidence-Based Audit 2.0.0-alpha.3')


if __name__ == '__main__':
    main()
