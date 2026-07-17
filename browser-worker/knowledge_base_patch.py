from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
REF_PATH = Path('/app/reference_model.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')
EXEC_PATH = Path('/app/executive_intelligence.py')
DASH_PATH = Path('/app/management_report_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    ref = REF_PATH.read_text(encoding='utf-8')
    ref = once(
        ref,
        'from evidence_engine import build_evidence_audit\n',
        'from evidence_engine import build_evidence_audit\nfrom knowledge_base import enrich_reference_audit\n',
        'knowledge base import',
    )
    ref = once(
        ref,
        '    folder = artifacts_dir / "reference-audit"\n',
        '    result = enrich_reference_audit(result)\n    folder = artifacts_dir / "reference-audit"\n',
        'reference audit knowledge enrichment',
    )
    ref = ref.replace('2.0.0-alpha.4', '2.0.0-alpha.5')
    REF_PATH.write_text(ref, encoding='utf-8')

    app = APP_PATH.read_text(encoding='utf-8')
    app = once(
        app,
        'from deep_rest_evidence import collect_deep_rest_evidence, read_latest_deep_rest_evidence',
        'from deep_rest_evidence import collect_deep_rest_evidence, read_latest_deep_rest_evidence\nfrom knowledge_base import get_catalog, get_module',
        'knowledge API imports',
    )
    marker = '''@app.get("/deep-rest-evidence/latest")
async def deep_rest_evidence_latest() -> dict[str, Any]:
    try:
        return read_latest_deep_rest_evidence(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return collect_deep_rest_evidence(settings.browser_artifacts_dir)
'''
    addition = marker + '''

@app.get("/knowledge-base")
async def knowledge_base_catalog() -> dict[str, Any]:
    return get_catalog()


@app.get("/knowledge-base/{capability_id}")
async def knowledge_base_module(capability_id: str) -> dict[str, Any]:
    try:
        return get_module(capability_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown knowledge module: {capability_id}")
'''
    app = once(app, marker, addition, 'knowledge API endpoints')
    app = app.replace('2.0.0-alpha.4', '2.0.0-alpha.5')
    APP_PATH.write_text(app, encoding='utf-8')

    dash = DASH_PATH.read_text(encoding='utf-8')
    needle = "<p><b class=\"bad\">'+(x.status==='missing'?'Не найдено подтверждений':esc(x.status||'Требует проверки'))+'</b> · '+esc(x.domain||'')+' · уверенность '+Math.round(Number(x.confidence||0)*100)+'%</p>"
    replacement = needle + "+((x.methodology||{}).recommendation?'<p><b>Рекомендация по методике:</b> '+esc(x.methodology.recommendation)+'</p>':'')"
    if needle in dash:
        dash = dash.replace(needle, replacement, 1)
    DASH_PATH.write_text(dash, encoding='utf-8')

    for path in (ADMIN_PATH, EXEC_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.4', '2.0.0-alpha.5')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Knowledge Base & Methodology 2.0.0-alpha.5')


if __name__ == '__main__':
    main()
