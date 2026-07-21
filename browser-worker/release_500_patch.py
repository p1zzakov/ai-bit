from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
AUDIT = Path('/app/bitrix_onec_integration_audit.py')
DASHBOARD = Path('/app/bitrix_onec_integration_dashboard.py')
SOURCE = Path('/app/source_provider.py')


def patch_audit(text: str) -> str:
    marker = 'from dual_integration_reporting import enrich_with_dual_reports\n'
    if 'from platform_core_v5 import build_platform_v5' not in text:
        if marker not in text:
            raise RuntimeError('5.0.0 dual reporting import anchor not found')
        text = text.replace(marker, marker + 'from platform_core_v5 import build_platform_v5\n', 1)
    anchor = '    verification_pipeline = enrich_with_dual_reports(verification_pipeline)\n'
    addition = anchor + '    verification_pipeline["platform_v5"] = build_platform_v5(verification_pipeline)\n'
    if addition not in text:
        if anchor not in text:
            raise RuntimeError('5.0.0 dual reporting assignment anchor not found')
        text = text.replace(anchor, addition, 1)
    text = text.replace('VERSION = "4.7.0"', 'VERSION = "5.0.0"')
    return text


def patch_dashboard(text: str) -> str:
    text = text.replace('AI-BIT Enterprise 4.7.0', 'AI-BIT Enterprise 5.0.0')
    text = text.replace(
        '<button class="tab" data-view="management">Для руководства</button>',
        '<button class="tab" data-view="platform5">Платформа 5.0</button><button class="tab" data-view="management">Для руководства</button>',
        1,
    )
    text = text.replace(
        '<section id="management" class="view"></section>',
        '<section id="platform5" class="view"></section><section id="management" class="view"></section>',
        1,
    )
    text = text.replace(
        'mgmt=p.management_conclusion||{},tech=p.technical_conclusion_v2||{};',
        'mgmt=p.management_conclusion||{},tech=p.technical_conclusion_v2||{},v5=p.platform_v5||{},eng=v5.engines||{};',
        1,
    )
    anchor = "q('#management').innerHTML="
    if anchor in text and "q('#platform5').innerHTML" not in text:
        js = '''q('#platform5').innerHTML=panel('AI-BIT Enterprise 5.0',`<div class="grid" style="padding:10px"><div class="card"><h3>Unified Intelligence Core</h3>${kv({'Версия':v5.version||'—','Редакция':v5.edition||'—','Статус':v5.status||'—','Режим':v5.mode||'read_only'})}</div><div class="card"><h3>Governance</h3>${kv(v5.governance||{})}</div></div>`)+panel('Движки платформы',table(['Движок','Статус','Назначение'],[['Evidence Engine 2.0',(eng.evidence||{}).status,'Доказательная база и confidence'],['Data Quality Engine',(eng.data_quality||{}).status,'Сверка фактических данных'],['Drift Detection',(eng.drift_detection||{}).status,'Контроль изменений интеграции'],['Business Impact',(eng.business_impact||{}).status,'Влияние на бизнес'],['Integrator Copilot',(eng.integrator_copilot||{}).status,'Проектирование и приёмка']].map(x=>`<tr><td><b>${esc(x[0])}</b></td><td>${badge(x[1])}</td><td>${esc(x[2])}</td></tr>`)),`${Object.keys(eng).length} engines`)+panel('Evidence Engine 2.0',table(['Finding','Severity','Confidence','Decision','Hash'],((eng.evidence||{}).bundles||[]).map(x=>`<tr><td><b>${esc(x.title||x.finding_code)}</b></td><td>${badge(x.severity)}</td><td>${Math.round((x.confidence||0)*100)}%</td><td>${badge(x.decision)}</td><td class="mono">${esc(x.evidence_hash||'—')}</td></tr>`)),`${((eng.evidence||{}).bundles||[]).length} bundles`)+panel('Data Quality',`<div style="padding:14px"><p>${esc((eng.data_quality||{}).note||'')}</p>${table(['ID','Проверка','Статус'],((eng.data_quality||{}).checks||[]).map(x=>`<tr><td class="mono">${esc(x.id)}</td><td>${esc(x.title)}</td><td>${badge(x.status)}</td></tr>`))}</div>`)+panel('Drift Detection',`<div style="padding:14px">${kv({'Статус':(eng.drift_detection||{}).status||'—','Snapshot':(eng.drift_detection||{}).snapshot_id||'—','Fingerprint':(eng.drift_detection||{}).fingerprint||'—'})}<p>${esc((eng.drift_detection||{}).note||'')}</p></div>`)+panel('Integrator Copilot',table(['Приоритет','Задача','Почему','Приёмка'],((eng.integrator_copilot||{}).playbooks||[]).map(x=>`<tr><td>${esc(x.priority)}</td><td><b>${esc(x.title)}</b></td><td>${esc(x.why)}</td><td>${esc(x.acceptance_test)}</td></tr>`)),`${((eng.integrator_copilot||{}).playbooks||[]).length} playbooks`);'''
        text = text.replace(anchor, js + anchor, 1)
    return text


def replace_public_version(text: str) -> str:
    for old in ('4.7.0', '4.6.0', '4.5.0', '4.4.0', '4.3.3', '4.3.2', '4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, '5.0.0')
    return text


def main() -> None:
    AUDIT.write_text(patch_audit(AUDIT.read_text(encoding='utf-8')), encoding='utf-8')
    DASHBOARD.write_text(patch_dashboard(DASHBOARD.read_text(encoding='utf-8')), encoding='utf-8')
    if SOURCE.exists():
        SOURCE.write_text(SOURCE.read_text(encoding='utf-8').replace('VERSION = "4.7.0"', 'VERSION = "5.0.0"'), encoding='utf-8')
    for path in (APP, ADMIN, MANIFEST):
        if path.exists():
            path.write_text(replace_public_version(path.read_text(encoding='utf-8')), encoding='utf-8')
    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8').replace('EDITION = "Dual-Layer Integration Conclusion"', 'EDITION = "Unified Integration Intelligence Platform"')
        MANIFEST.write_text(manifest, encoding='utf-8')
    required = {
        AUDIT: ('build_platform_v5(', '"platform_v5"', 'VERSION = "5.0.0"'),
        DASHBOARD: ('AI-BIT Enterprise 5.0.0', 'data-view="platform5"', 'Evidence Engine 2.0'),
    }
    for path, markers in required.items():
        compiled = path.read_text(encoding='utf-8')
        missing = [marker for marker in markers if marker not in compiled]
        if missing:
            raise RuntimeError(f'5.0.0 patch incomplete for {path.name}: {missing}')
    print('Applied AI-BIT Enterprise 5.0.0 — Unified Integration Intelligence Platform')


if __name__ == '__main__':
    main()
