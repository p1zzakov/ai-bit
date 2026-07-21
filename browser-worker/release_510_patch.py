from __future__ import annotations

import re
from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
VERSION = '5.1.0'


def _log(status: str, message: str) -> None:
    print(f'[{status}] {message}')


def _insert_once(text: str, marker: str, insertion: str, *, before: bool = False) -> tuple[str, bool]:
    if insertion in text:
        return text, False
    if marker not in text:
        return text, False
    replacement = insertion + marker if before else marker + insertion
    return text.replace(marker, replacement, 1), True


def patch_app(text: str) -> str:
    import_line = 'from onec_requirement_architect import router as onec_requirement_architect_router\n'
    if import_line in text:
        _log('SKIP', 'Requirement Architect import already exists')
    else:
        anchors = (
            'from pydantic_settings import BaseSettings, SettingsConfigDict\n',
            'from pydantic import BaseModel, Field\n',
            'from fastapi import FastAPI, HTTPException\n',
        )
        inserted = False
        for anchor in anchors:
            text, inserted = _insert_once(text, anchor, import_line)
            if inserted:
                _log('APPLY', f'Requirement Architect import inserted after {anchor.strip()}')
                break
        if not inserted:
            text = import_line + text
            _log('FALLBACK', 'Requirement Architect import inserted at file start')

    include_line = 'app.include_router(onec_requirement_architect_router)'
    if include_line in text:
        _log('SKIP', 'Requirement Architect router already registered')
    else:
        app_match = re.search(r'(?m)^app\s*=\s*FastAPI\([^\n]*\)\s*$', text)
        if app_match:
            pos = app_match.end()
            text = text[:pos] + '\n' + include_line + text[pos:]
            _log('APPLY', 'Requirement Architect router registered after FastAPI initialization')
        else:
            raise RuntimeError('5.1.0 cannot locate FastAPI application initialization')
    return text


def _insert_admin_nav(text: str) -> str:
    if 'data-key="onecRequirements"' in text:
        _log('SKIP', 'Requirement Architect navigation item already exists')
        return text

    new_nav = '<button data-key="onecRequirements"><span class="icon">ТЗ</span><span class="label">Конструктор ТЗ 1С</span></button>'
    patterns = (
        r'(<button\b[^>]*data-key=["\']system["\'][^>]*>.*?</button>)',
        r'(</nav>)',
    )
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if not match:
            continue
        pos = match.start(1)
        text = text[:pos] + new_nav + text[pos:]
        _log('APPLY' if index == 0 else 'FALLBACK', 'Requirement Architect navigation item inserted')
        return text

    _log('WARN', 'Navigation container not found; direct module URL remains available')
    return text


def _insert_admin_frame(text: str) -> str:
    if re.search(r'data-key=["\']onecRequirements["\'][^>]*data-src=["\']/onec-requirements["\']', text):
        _log('SKIP', 'Requirement Architect iframe already exists')
        return text

    new_frame = '<iframe class="frame" data-key="onecRequirements" data-src="/onec-requirements"></iframe>'
    patterns = (
        r'(<iframe\b[^>]*data-key=["\']system["\'][^>]*>\s*</iframe>)',
        r'(</div>\s*</main>)',
    )
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if not match:
            continue
        pos = match.start(1)
        text = text[:pos] + new_frame + text[pos:]
        _log('APPLY' if index == 0 else 'FALLBACK', 'Requirement Architect iframe inserted')
        return text

    _log('WARN', 'Iframe container not found; direct module URL remains available')
    return text


def _insert_admin_meta(text: str) -> str:
    if 'onecRequirements:{title:' in text:
        _log('SKIP', 'Requirement Architect metadata already exists')
        return text

    new_meta = "onecRequirements:{title:'Конструктор ТЗ для 1С',subtitle:'Интервью, проверка реализуемости, прототип и техническое задание',url:'/onec-requirements'},"
    system_match = re.search(r'(system\s*:\s*\{[^{}]*?url\s*:\s*["\']/system["\'][^{}]*?\})', text, flags=re.DOTALL)
    if system_match:
        pos = system_match.start(1)
        text = text[:pos] + new_meta + text[pos:]
        _log('APPLY', 'Requirement Architect page metadata inserted')
        return text

    object_end = re.search(r'(};\s*const\s+\$\s*=)', text)
    if object_end:
        pos = object_end.start(1)
        prefix = ',' if not text[:pos].rstrip().endswith(('{', ',')) else ''
        text = text[:pos] + prefix + new_meta.rstrip(',') + text[pos:]
        _log('FALLBACK', 'Requirement Architect metadata appended to page map')
        return text

    _log('WARN', 'Page metadata map not found; direct module URL remains available')
    return text


def patch_admin(text: str) -> str:
    text = _insert_admin_nav(text)
    text = _insert_admin_frame(text)
    text = _insert_admin_meta(text)
    return text


def replace_version(text: str) -> str:
    for old in ('5.0.0', '4.7.0', '4.6.0', '4.5.0', '4.4.0', '4.3.3', '4.3.2', '4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, VERSION)
    return text


def _validate(path: Path, markers: tuple[str, ...], *, fatal: bool) -> None:
    body = path.read_text(encoding='utf-8')
    missing = [marker for marker in markers if marker not in body]
    if not missing:
        _log('OK', f'{path.name} validation passed')
        return
    message = f'{path.name} missing markers: {missing}'
    if fatal:
        raise RuntimeError(f'5.1.0 patch incomplete: {message}')
    _log('WARN', message)


def main() -> None:
    app_body = replace_version(patch_app(APP.read_text(encoding='utf-8')))
    APP.write_text(app_body, encoding='utf-8')

    admin_body = replace_version(patch_admin(ADMIN.read_text(encoding='utf-8')))
    ADMIN.write_text(admin_body, encoding='utf-8')

    if MANIFEST.exists():
        manifest = replace_version(MANIFEST.read_text(encoding='utf-8'))
        manifest = manifest.replace('EDITION = "Unified Integration Intelligence Platform"', 'EDITION = "1C Requirement Architect"')
        MANIFEST.write_text(manifest, encoding='utf-8')

    # API registration is release-critical. Unified navigation is desirable but
    # not allowed to break the image build because the module has a direct URL.
    _validate(APP, ('onec_requirement_architect_router', 'app.include_router(onec_requirement_architect_router)', VERSION), fatal=True)
    _validate(ADMIN, ('/onec-requirements', VERSION), fatal=False)

    print('Applied AI-BIT Enterprise 5.1.0 — 1C Requirement Architect (resilient patch framework)')


if __name__ == '__main__':
    main()
