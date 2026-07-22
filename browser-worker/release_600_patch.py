from __future__ import annotations

import re
from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')


def log(state: str, message: str) -> None:
    print(f'[{state}] {message}')


def patch_app(text: str) -> str:
    import_line = 'from project_intelligence import router as project_intelligence_router\n'
    if import_line not in text:
        anchors = (
            'from onec_requirement_architect import router as onec_requirement_architect_router\n',
            'from pydantic_settings import BaseSettings, SettingsConfigDict\n',
        )
        anchor = next((x for x in anchors if x in text), None)
        if not anchor:
            raise RuntimeError('6.0.0 app import anchor not found')
        text = text.replace(anchor, anchor + import_line, 1)
        log('APPLY', 'Project Intelligence import inserted')
    else:
        log('SKIP', 'Project Intelligence import already present')

    include_line = 'app.include_router(project_intelligence_router)'
    if include_line not in text:
        known = 'app.include_router(onec_requirement_architect_router)'
        if known in text:
            text = text.replace(known, known + '\n' + include_line, 1)
        else:
            match = re.search(r'app\s*=\s*FastAPI\([^\n]+\)', text)
            if not match:
                raise RuntimeError('6.0.0 FastAPI application anchor not found')
            text = text[:match.end()] + '\n' + include_line + text[match.end():]
        log('APPLY', 'Project Intelligence router registered')
    else:
        log('SKIP', 'Project Intelligence router already registered')
    return text


def patch_admin(text: str) -> str:
    nav = '<button data-key="projectIntelligence"><span class="icon">PI</span><span class="label">AI Project Analyst</span></button>'
    if 'data-key="projectIntelligence"' not in text:
        patterns = (
            r'(<button[^>]+data-key="onecRequirements"[^>]*>)',
            r'(<button[^>]+data-key="system"[^>]*>)',
            r'(</nav>)',
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                text = text[:match.start()] + nav + text[match.start():]
                log('APPLY', 'Project Intelligence navigation inserted')
                break
        else:
            log('WARN', 'Navigation anchor not found; direct route remains available')
    else:
        log('SKIP', 'Project Intelligence navigation already present')

    frame = '<iframe class="frame" data-key="projectIntelligence" data-src="/project-intelligence"></iframe>'
    if 'data-key="projectIntelligence" data-src="/project-intelligence"' not in text:
        patterns = (
            r'(<iframe[^>]+data-key="onecRequirements"[^>]*></iframe>)',
            r'(<iframe[^>]+data-key="system"[^>]*></iframe>)',
            r'(</div></main></section>)',
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                text = text[:match.start()] + frame + text[match.start():]
                log('APPLY', 'Project Intelligence iframe inserted')
                break
        else:
            log('WARN', 'Iframe anchor not found; direct route remains available')
    else:
        log('SKIP', 'Project Intelligence iframe already present')

    meta = "projectIntelligence:{title:'AI Project Analyst',subtitle:'Материалы, требования, интервью, MCP-проверка и комплект документов',url:'/project-intelligence'},"
    if 'projectIntelligence:{title:' not in text:
        patterns = (
            r'(onecRequirements:\{title:)',
            r'(system:\{title:)',
            r'(const meta=\{)',
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                text = text[:match.start()] + meta + text[match.start():]
                log('APPLY', 'Project Intelligence metadata inserted')
                break
        else:
            log('WARN', 'Page metadata anchor not found; direct route remains available')
    else:
        log('SKIP', 'Project Intelligence metadata already present')
    return text


def replace_version(text: str) -> str:
    versions = ('5.1.0', '5.0.0', '4.7.0', '4.6.0', '4.5.0', '4.4.0', '4.3.3', '3.2.1')
    for old in versions:
        text = text.replace(old, '6.0.0')
    return text


def main() -> None:
    APP.write_text(replace_version(patch_app(APP.read_text(encoding='utf-8'))), encoding='utf-8')
    ADMIN.write_text(replace_version(patch_admin(ADMIN.read_text(encoding='utf-8'))), encoding='utf-8')
    if MANIFEST.exists():
        manifest = replace_version(MANIFEST.read_text(encoding='utf-8'))
        manifest = re.sub(r'EDITION\s*=\s*"[^"]*"', 'EDITION = "Project Intelligence Platform"', manifest, count=1)
        MANIFEST.write_text(manifest, encoding='utf-8')

    app_body = APP.read_text(encoding='utf-8')
    required = ('project_intelligence_router', 'app.include_router(project_intelligence_router)', '6.0.0')
    missing = [x for x in required if x not in app_body]
    if missing:
        raise RuntimeError(f'6.0.0 critical app validation failed: {missing}')
    log('OK', 'app.py validation passed')

    admin_body = ADMIN.read_text(encoding='utf-8')
    if '/project-intelligence' in admin_body:
        log('OK', 'admin navigation validation passed')
    else:
        log('WARN', 'admin navigation unavailable; use /project-intelligence directly')
    print('Applied AI-BIT Enterprise 6.0.0 — Project Intelligence Platform')


if __name__ == '__main__':
    main()
