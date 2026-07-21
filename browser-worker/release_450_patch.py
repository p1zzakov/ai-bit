from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
AUDIT = Path('/app/bitrix_onec_integration_audit.py')
SOURCE = Path('/app/source_provider.py')
DASHBOARD = Path('/app/bitrix_onec_integration_dashboard.py')


def patch_source(text: str) -> str:
    if 'from active_integration_analysis import augment_active_calls' not in text:
        text = text.replace(
            'from integration_verification_pipeline import augment_onec_calls\n',
            'from integration_verification_pipeline import augment_onec_calls\nfrom active_integration_analysis import augment_active_calls\n',
            1,
        )
    anchor = '        self.calls = augment_onec_calls(self.provider_id, self.allowed_tools, self.calls)'
    addition = anchor + '\n        self.calls = augment_active_calls(self.provider_id, self.allowed_tools, self.calls)'
    if addition not in text:
        if anchor not in text:
            raise RuntimeError('4.5.0 source provider anchor not found')
        text = text.replace(anchor, addition, 1)
    text = text.replace('VERSION = "4.4.0"', 'VERSION = "4.5.0"')
    return text


def patch_audit(text: str) -> str:
    if 'from active_integration_analysis import enrich_verification_pipeline' not in text:
        text = text.replace(
            'from integration_verification_pipeline import DISCOVERY_CALLS, build_verification_pipeline\n',
            'from integration_verification_pipeline import DISCOVERY_CALLS, build_verification_pipeline\nfrom active_integration_analysis import enrich_verification_pipeline\n',
            1,
        )
    anchor = '    verification_pipeline = build_verification_pipeline(bitrix, onec)'
    addition = anchor + '\n    verification_pipeline = enrich_verification_pipeline(verification_pipeline, bitrix, onec)'
    if addition not in text:
        if anchor not in text:
            raise RuntimeError('4.5.0 verification pipeline anchor not found')
        text = text.replace(anchor, addition, 1)
    text = text.replace('VERSION = "4.4.0"', 'VERSION = "4.5.0"')
    return text


def patch_dashboard(text: str) -> str:
    text = text.replace('AI-BIT Enterprise 4.4.0', 'AI-BIT Enterprise 4.5.0')
    text = text.replace(
        '<button class="tab" data-view="mappings">Сущности</button><button class="tab" data-view="artifacts">Точки интеграции</button>',
        '<button class="tab" data-view="mappings">Сущности</button><button class="tab" data-view="fields">Поля</button><button class="tab" data-view="artifacts">Точки интеграции</button>',
        1,
    )
    text = text.replace(
        '<section id="mappings" class="view"></section><section id="artifacts" class="view"></section>',
        '<section id="mappings" class="view"></section><section id="fields" class="view"></section><section id="artifacts" class="view"></section>',
        1,
    )
    text = text.replace(
        'maps=p.entity_mappings||[],arts=p.integration_artifacts||[],calls=p.verification_calls||[],',
        'maps=p.entity_mappings||[],rawArts=p.integration_artifacts||[],arts=p.active_integration_artifacts||rawArts,fields=p.field_mappings||[],calls=p.verification_calls||[],',
        1,
    )
    mapping_end = ')),`${maps.length} mappings`);q(\'#artifacts\').innerHTML='
    field_render = ''')),`${maps.length} mappings`);q('#fields').innerHTML=panel('Кандидаты сопоставления полей',table(['Статус','Сущность','Смысл','Поле Bitrix24','Поле 1С','Evidence'],fields.map(x=>`<tr><td>${badge(x.status)}</td><td><b>${esc(x.entity_label||x.entity_id)}</b></td><td class="mono">${esc(x.semantic)}</td><td class="mono">${esc(x.bitrix_field||'—')}</td><td class="mono">${esc(x.onec_field||'—')}</td><td>${x.bitrix_evidence?'BX ':''}${x.onec_evidence?'1C':''}</td></tr>`)),`${fields.length} fields`);q('#artifacts').innerHTML='''
    if mapping_end in text and "Кандидаты сопоставления полей" not in text:
        text = text.replace(mapping_end, field_render, 1)
    text = text.replace('Обнаруженные технические точки интеграции', 'Приоритетные технические точки интеграции')
    text = text.replace('`${arts.length} artifacts`)', '`${arts.length} active / ${rawArts.length} raw`)', 1)
    return text


def replace_public_version(text: str) -> str:
    for old in ('4.4.0', '4.3.3', '4.3.2', '4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, '4.5.0')
    return text


def main() -> None:
    SOURCE.write_text(patch_source(SOURCE.read_text(encoding='utf-8')), encoding='utf-8')
    AUDIT.write_text(patch_audit(AUDIT.read_text(encoding='utf-8')), encoding='utf-8')
    DASHBOARD.write_text(patch_dashboard(DASHBOARD.read_text(encoding='utf-8')), encoding='utf-8')
    for path in (APP, ADMIN, MANIFEST):
        if path.exists():
            path.write_text(replace_public_version(path.read_text(encoding='utf-8')), encoding='utf-8')
    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8')
        manifest = manifest.replace('EDITION = "Integration Verification Pipeline"', 'EDITION = "Active Integration Analysis"')
        MANIFEST.write_text(manifest, encoding='utf-8')
    required = {
        SOURCE: ('augment_active_calls(', 'VERSION = "4.5.0"'),
        AUDIT: ('enrich_verification_pipeline(', 'VERSION = "4.5.0"'),
        DASHBOARD: ('AI-BIT Enterprise 4.5.0', 'data-view="fields"'),
    }
    for path, markers in required.items():
        compiled = path.read_text(encoding='utf-8')
        missing = [marker for marker in markers if marker not in compiled]
        if missing:
            raise RuntimeError(f'4.5.0 patch incomplete for {path.name}: {missing}')
    print('Applied AI-BIT Enterprise 4.5.0 — Active Integration Analysis')


if __name__ == '__main__':
    main()
