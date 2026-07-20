from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')

ROUTES = r'''

from fastapi.responses import PlainTextResponse as BlueprintPlainTextResponse
from implementation_blueprint import build_implementation_blueprint, blueprint_markdown

@app.get("/implementation-blueprint/latest")
def implementation_blueprint_latest() -> dict[str, Any]:
    return build_implementation_blueprint(settings.browser_artifacts_dir)

@app.get("/implementation-blueprint/spec.md", response_class=BlueprintPlainTextResponse)
def implementation_blueprint_spec() -> BlueprintPlainTextResponse:
    blueprint = build_implementation_blueprint(settings.browser_artifacts_dir)
    return BlueprintPlainTextResponse(
        blueprint_markdown(blueprint),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=bitrix24-technical-specification.md"},
    )
'''


def replace(path: Path, pairs: tuple[tuple[str, str], ...]) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')


def main() -> None:
    app = APP.read_text(encoding='utf-8')
    if '@app.get("/implementation-blueprint/latest")' not in app:
        app += ROUTES
    for old in ('"version": "3.5.0"', '"version": "3.4.2"', '"version": "3.4.0"'):
        app = app.replace(old, '"version": "3.5.1"')
    APP.write_text(app, encoding='utf-8')

    replace(ADMIN, (('AI-BIT · 3.5.0', 'AI-BIT · 3.5.1'),))
    replace(MANIFEST, (
        ('VERSION = "3.5.0"', 'VERSION = "3.5.1"'),
        ('EDITION = "Bitrix24 Engineering Audit"', 'EDITION = "Implementation Blueprint"'),
    ))
    print('Applied AI-BIT Enterprise 3.5.1 — Read-Only Implementation Blueprint')


if __name__ == '__main__':
    main()
