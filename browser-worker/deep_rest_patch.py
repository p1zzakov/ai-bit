from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')
EXEC_PATH = Path('/app/executive_intelligence.py')
REF_PATH = Path('/app/reference_model.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    app = APP_PATH.read_text(encoding='utf-8')
    app = once(
        app,
        'from evidence_engine import build_evidence_audit, read_latest_evidence_audit',
        'from evidence_engine import build_evidence_audit, read_latest_evidence_audit\nfrom deep_rest_evidence import collect_deep_rest_evidence, read_latest_deep_rest_evidence',
        'deep REST imports',
    )
    marker = '''@app.get("/evidence-audit/latest")
async def evidence_audit_latest() -> dict[str, Any]:
    try:
        return read_latest_evidence_audit(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return build_evidence_audit(settings.browser_artifacts_dir)
'''
    addition = marker + '''

@app.post("/deep-rest-evidence/collect")
async def deep_rest_evidence_collect() -> dict[str, Any]:
    return collect_deep_rest_evidence(settings.browser_artifacts_dir)


@app.get("/deep-rest-evidence/latest")
async def deep_rest_evidence_latest() -> dict[str, Any]:
    try:
        return read_latest_deep_rest_evidence(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return collect_deep_rest_evidence(settings.browser_artifacts_dir)
'''
    app = once(app, marker, addition, 'deep REST endpoints')
    app = app.replace('2.0.0-alpha.3', '2.0.0-alpha.4')
    APP_PATH.write_text(app, encoding='utf-8')

    for path in (ADMIN_PATH, EXEC_PATH, REF_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.3', '2.0.0-alpha.4')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Deep REST Evidence 2.0.0-alpha.4')


if __name__ == '__main__':
    main()
