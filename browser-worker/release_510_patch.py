from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')


def patch_app(text: str) -> str:
    import_anchor = 'from pydantic_settings import BaseSettings, SettingsConfigDict\n'
    import_line = 'from onec_requirement_architect import router as onec_requirement_architect_router\n'
    if import_line not in text:
        if import_anchor not in text:
            raise RuntimeError('5.1.0 app import anchor not found')
        text = text.replace(import_anchor, import_anchor + import_line, 1)
    app_patterns = (
        'app = FastAPI(title="AI-BIT Browser Worker", version="5.0.0")',
        'app = FastAPI(title="AI-BIT Browser Worker", version="0.2.0")',
    )
    app_anchor = next((x for x in app_patterns if x in text), None)
    include_line = 'app.include_router(onec_requirement_architect_router)'
    if include_line not in text:
        if not app_anchor:
            raise RuntimeError('5.1.0 FastAPI anchor not found')
        text = text.replace(app_anchor, app_anchor + '\n' + include_line, 1)
    return text


def patch_admin(text: str) -> str:
    nav_anchor = '<button data-key="system"><span class="icon">S</span><span class="label">Система</span></button>'
    new_nav = '<button data-key="onecRequirements"><span class="icon">ТЗ</span><span class="label">Конструктор ТЗ 1С</span></button>' + nav_anchor
    if 'data-key="onecRequirements"' not in text:
        if nav_anchor not in text:
            raise RuntimeError('5.1.0 admin nav anchor not found')
        text = text.replace(nav_anchor, new_nav, 1)
    frame_anchor = '<iframe class="frame" data-key="system" data-src="/system"></iframe>'
    new_frame = '<iframe class="frame" data-key="onecRequirements" data-src="/onec-requirements"></iframe>' + frame_anchor
    if 'data-key="onecRequirements" data-src="/onec-requirements"' not in text:
        if frame_anchor not in text:
            raise RuntimeError('5.1.0 admin frame anchor not found')
        text = text.replace(frame_anchor, new_frame, 1)
    meta_anchor = "system:{title:'Система и качество данных',subtitle:'Источники, права, свежесть и диагностика',url:'/system'}"
    new_meta = "onecRequirements:{title:'Конструктор ТЗ для 1С',subtitle:'Интервью, проверка реализуемости, прототип и техническое задание',url:'/onec-requirements'}," + meta_anchor
    if 'onecRequirements:{title:' not in text:
        if meta_anchor not in text:
            raise RuntimeError('5.1.0 admin metadata anchor not found')
        text = text.replace(meta_anchor, new_meta, 1)
    return text


def replace_version(text: str) -> str:
    for old in ('5.0.0', '4.7.0', '4.6.0', '4.5.0', '4.4.0', '4.3.3', '3.2.1'):
        text = text.replace(old, '5.1.0')
    return text


def main() -> None:
    APP.write_text(replace_version(patch_app(APP.read_text(encoding='utf-8'))), encoding='utf-8')
    ADMIN.write_text(replace_version(patch_admin(ADMIN.read_text(encoding='utf-8'))), encoding='utf-8')
    if MANIFEST.exists():
        manifest = replace_version(MANIFEST.read_text(encoding='utf-8'))
        manifest = manifest.replace('EDITION = "Unified Integration Intelligence Platform"', 'EDITION = "1C Requirement Architect"')
        MANIFEST.write_text(manifest, encoding='utf-8')
    checks = {
        APP: ('onec_requirement_architect_router', 'app.include_router(onec_requirement_architect_router)', '5.1.0'),
        ADMIN: ('data-key="onecRequirements"', '/onec-requirements', 'AI-BIT · 5.1.0'),
    }
    for path, markers in checks.items():
        body = path.read_text(encoding='utf-8')
        missing = [marker for marker in markers if marker not in body]
        if missing:
            raise RuntimeError(f'5.1.0 patch incomplete for {path.name}: {missing}')
    print('Applied AI-BIT Enterprise 5.1.0 — 1C Requirement Architect')


if __name__ == '__main__':
    main()
