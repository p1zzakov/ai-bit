from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
AUDIT = Path('/app/bitrix_onec_integration_audit.py')
DASHBOARD = Path('/app/bitrix_onec_integration_dashboard.py')
SOURCE = Path('/app/source_provider.py')


def patch_audit(text: str) -> str:
    marker = 'from best_practice_integration_assessment import build_best_practice_assessment\n'
    if 'from dual_integration_reporting import enrich_with_dual_reports' not in text:
        if marker not in text:
            raise RuntimeError('4.7.0 assessment import anchor not found')
        text = text.replace(marker, marker + 'from dual_integration_reporting import enrich_with_dual_reports\n', 1)
    anchor = '    verification_pipeline["best_practice_assessment"] = best_practice_assessment\n'
    addition = anchor + '    verification_pipeline = enrich_with_dual_reports(verification_pipeline)\n'
    if addition not in text:
        if anchor not in text:
            raise RuntimeError('4.7.0 assessment assignment anchor not found')
        text = text.replace(anchor, addition, 1)
    text = text.replace('VERSION = "4.6.0"', 'VERSION = "4.7.0"')
    return text


def patch_dashboard(text: str) -> str:
    text = text.replace('AI-BIT Enterprise 4.6.0', 'AI-BIT Enterprise 4.7.0')
    text = text.replace(
        '<button class="tab" data-view="assessment">Оценка</button>',
        '<button class="tab" data-view="management">Для руководства</button><button class="tab" data-view="technical">Технический акт</button><button class="tab" data-view="assessment">Оценка</button>',
        1,
    )
    text = text.replace(
        '<section id="assessment" class="view"></section>',
        '<section id="management" class="view"></section><section id="technical" class="view"></section><section id="assessment" class="view"></section>',
        1,
    )
    text = text.replace(
        'sum=data.summary||{},ass=p.best_practice_assessment||{},dims=ass.dimensions||[],bpFindings=ass.confirmed_findings||[],recs=ass.recommendations||[];',
        'sum=data.summary||{},ass=p.best_practice_assessment||{},dims=ass.dimensions||[],bpFindings=ass.confirmed_findings||[],recs=ass.recommendations||[],mgmt=p.management_conclusion||{},tech=p.technical_conclusion_v2||{};',
        1,
    )
    anchor = "q('#assessment').innerHTML="
    if anchor in text and "q('#management').innerHTML" not in text:
        js = '''q('#management').innerHTML=panel('Управленческое заключение',`<div class="grid" style="padding:10px"><div class="card"><h3>Итог</h3>${kv({'Оценка':mgmt.quality_score??'—','Заключение':mgmt.verdict_text||'—','Промышленный допуск':mgmt.industrial_admission_text||'—'})}<p style="margin-top:12px">${esc(mgmt.executive_summary||'')}</p></div><div class="card"><h3>Что уже работает</h3>${(mgmt.what_works||[]).map(x=>`<div class="row"><span>✓</span><b>${esc(x)}</b></div>`).join('')||'<div class="empty">Подтверждённых положительных фактов пока нет.</div>'}</div></div>`)+panel('Что работает неправильно и почему это важно',table(['Приоритет','Проблема','Что не так','Последствия','Что сделать','Результат'],(mgmt.problems||[]).map(x=>`<tr><td>${badge(x.severity)}</td><td><b>${esc(x.title)}</b></td><td>${esc(x.what_is_wrong)}</td><td>${esc(x.why_it_matters)}</td><td>${esc(x.what_to_do)}</td><td>${esc(x.result_after_fix)}</td></tr>`)),`${(mgmt.problems||[]).length} проблем`)+panel('План исправления',table(['Шаг','Приоритет','Действие','Зачем','Готово, когда'],(mgmt.roadmap||[]).map(x=>`<tr><td class="mono">${esc(x.step)}</td><td>${badge(x.priority)}</td><td><b>${esc(x.title)}</b></td><td>${esc(x.why)}</td><td>${esc(x.done_when)}</td></tr>`)),`${(mgmt.roadmap||[]).length} шагов`)+panel('Проверка выгрузки',`<div style="padding:14px"><b>${esc(mgmt.data_validation_message||'')}</b></div>`);
q('#technical').innerHTML=panel('Технический акт проверки',`<div class="grid" style="padding:10px"><div class="card"><h3>Область проверки</h3>${(tech.scope||[]).map(x=>`<div class="row"><span>${esc(x)}</span><b>read-only</b></div>`).join('')}</div><div class="card"><h3>Метод</h3><p>${esc(tech.method||'')}</p>${kv({'Версия':tech.version||'—','Аудитория':tech.audience||'—','Решение по допуску':(tech.release_gate||{}).decision||'—'})}</div></div>`)+panel('Подтверждённые несоответствия',table(['Код','Severity','Область','Что реализовано','Нарушенный принцип','Сценарий отказа','Требуемая реализация','Приёмочный тест'],(tech.confirmed_nonconformities||[]).map(x=>`<tr><td class="mono"><b>${esc(x.control_id)}</b></td><td>${badge(x.severity)}</td><td>${esc(x.area_label)}</td><td class="mono">${esc(x.observed_implementation)}</td><td>${esc(x.violated_principle)}</td><td>${esc((x.failure_scenarios||[]).join('; '))}</td><td>${esc(x.required_implementation)}</td><td>${esc(x.acceptance_test)}</td></tr>`)),`${(tech.confirmed_nonconformities||[]).length} controls`)+panel('Контроли, требующие подтверждения',table(['Код','Контроль','Статус','Почему не подтверждён','Какой evidence нужен'],(tech.controls_requiring_verification||[]).map(x=>`<tr><td class="mono">${esc(x.control_id)}</td><td><b>${esc(x.title)}</b></td><td>${badge(x.status)}</td><td>${esc(x.reason)}</td><td>${esc(x.required_evidence)}</td></tr>`)),`${(tech.controls_requiring_verification||[]).length} controls`)+panel('Матрица полей',table(['Сущность','Смысл','Bitrix24','1С','Статус','Evidence'],(tech.field_mapping_matrix||[]).map(x=>`<tr><td><b>${esc(x.entity)}</b></td><td class="mono">${esc(x.semantic)}</td><td class="mono">${esc(x.bitrix_field||'—')}</td><td class="mono">${esc(x.onec_field||'—')}</td><td>${badge(x.status)}</td><td>${x.bitrix_evidence?'BX ':''}${x.onec_evidence?'1C':''}</td></tr>`)),`${(tech.field_mapping_matrix||[]).length} mappings`)+panel('Критерии допуска',`<div style="padding:14px">${((tech.release_gate||{}).blocking_conditions||[]).map((x,i)=>`<div class="row"><span>${i+1}</span><b>${esc(x)}</b></div>`).join('')}</div>`);
'''
        text = text.replace(anchor, js + anchor, 1)
    return text


def replace_public_version(text: str) -> str:
    for old in ('4.6.0', '4.5.0', '4.4.0', '4.3.3', '4.3.2', '4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, '4.7.0')
    return text


def main() -> None:
    AUDIT.write_text(patch_audit(AUDIT.read_text(encoding='utf-8')), encoding='utf-8')
    DASHBOARD.write_text(patch_dashboard(DASHBOARD.read_text(encoding='utf-8')), encoding='utf-8')
    if SOURCE.exists():
        SOURCE.write_text(SOURCE.read_text(encoding='utf-8').replace('VERSION = "4.6.0"', 'VERSION = "4.7.0"'), encoding='utf-8')
    for path in (APP, ADMIN, MANIFEST):
        if path.exists():
            path.write_text(replace_public_version(path.read_text(encoding='utf-8')), encoding='utf-8')
    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8').replace('EDITION = "Best-Practice Integration Assessment"', 'EDITION = "Dual-Layer Integration Conclusion"')
        MANIFEST.write_text(manifest, encoding='utf-8')
    required = {
        AUDIT: ('enrich_with_dual_reports(', 'VERSION = "4.7.0"'),
        DASHBOARD: ('AI-BIT Enterprise 4.7.0', 'data-view="management"', 'data-view="technical"', 'Технический акт проверки'),
    }
    for path, markers in required.items():
        compiled = path.read_text(encoding='utf-8')
        missing = [marker for marker in markers if marker not in compiled]
        if missing:
            raise RuntimeError(f'4.7.0 patch incomplete for {path.name}: {missing}')
    print('Applied AI-BIT Enterprise 4.7.0 — Dual-Layer Integration Conclusion')


if __name__ == '__main__':
    main()
