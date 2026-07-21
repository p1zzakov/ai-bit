from __future__ import annotations

from pathlib import Path

APP = Path('/app/app.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
AUDIT = Path('/app/bitrix_onec_integration_audit.py')
DASHBOARD = Path('/app/bitrix_onec_integration_dashboard.py')
SOURCE = Path('/app/source_provider.py')


def patch_audit(text: str) -> str:
    marker = 'from active_integration_analysis import enrich_verification_pipeline\n'
    if 'from best_practice_integration_assessment import build_best_practice_assessment' not in text:
        if marker not in text:
            raise RuntimeError('active integration import anchor not found')
        text = text.replace(marker, marker + 'from best_practice_integration_assessment import build_best_practice_assessment\n', 1)

    anchor = '    data_checks = _data_checks(onec)\n'
    addition = anchor + '''    best_practice_assessment = build_best_practice_assessment(
        verification_pipeline,
        data_checks=data_checks,
    )
    verification_pipeline["best_practice_assessment"] = best_practice_assessment
    verification_pipeline["findings"] = best_practice_assessment.get("confirmed_findings", [])
    verification_pipeline["technical_conclusion"] = {
        "status": best_practice_assessment.get("verdict"),
        "industrial_admission": best_practice_assessment.get("industrial_admission"),
        "overall_score": best_practice_assessment.get("overall_score"),
        "confirmed_findings": len(best_practice_assessment.get("confirmed_findings", [])),
        "severity_summary": best_practice_assessment.get("severity_summary", {}),
        "reason": "Заключение сформировано по подтверждённым evidence и контрольной модели лучших практик.",
    }
    verification_pipeline["status"] = (
        "critical_actions_required"
        if best_practice_assessment.get("severity_summary", {}).get("critical", 0)
        else "assessment_ready"
    )
'''
    if 'best_practice_assessment = build_best_practice_assessment(' not in text:
        if anchor not in text:
            raise RuntimeError('data checks anchor not found')
        text = text.replace(anchor, addition, 1)

    text = text.replace(
        '    findings: list[dict[str, Any]] = []\n    blueprint: list[dict[str, Any]] = []',
        '    findings: list[dict[str, Any]] = list(best_practice_assessment.get("confirmed_findings", []))\n    blueprint: list[dict[str, Any]] = list(best_practice_assessment.get("recommendations", []))',
        1,
    )
    text = text.replace('            "findings": 0,', '            "findings": len(findings),', 1)
    text = text.replace('VERSION = "4.5.0"', 'VERSION = "4.6.0"')
    return text


def patch_dashboard(text: str) -> str:
    text = text.replace('AI-BIT Enterprise 4.5.0', 'AI-BIT Enterprise 4.6.0')
    text = text.replace(
        '<button class="tab" data-view="verification">План проверки</button><button class="tab" data-view="findings">Заключение</button>',
        '<button class="tab" data-view="assessment">Оценка</button><button class="tab" data-view="verification">План проверки</button><button class="tab" data-view="findings">Заключение</button>',
        1,
    )
    text = text.replace(
        '<section id="verification" class="view"></section><section id="findings" class="view"></section>',
        '<section id="assessment" class="view"></section><section id="verification" class="view"></section><section id="findings" class="view"></section>',
        1,
    )
    text = text.replace(
        'prof=data.onec_profile||{},cfg=prof.configuration||{},mc=prof.metadata_counts||{},sum=data.summary||{};',
        'prof=data.onec_profile||{},cfg=prof.configuration||{},mc=prof.metadata_counts||{},sum=data.summary||{},ass=p.best_practice_assessment||{},dims=ass.dimensions||[],bpFindings=ass.confirmed_findings||[],recs=ass.recommendations||[];',
        1,
    )
    text = text.replace("['Findings',sum.findings||0]", "['Оценка',ass.overall_score??'—'],['Критично',(ass.severity_summary||{}).critical||0],['Findings',sum.findings||0]", 1)

    verification_anchor = "q('#verification').innerHTML=panel('Следующие read-only проверки'"
    if verification_anchor in text and "q('#assessment').innerHTML" not in text:
        assessment_js = '''q('#assessment').innerHTML=panel('Итоговая оценка',`<div class="grid" style="padding:10px"><div class="card"><h3>Заключение</h3>${kv({'Вердикт':ass.verdict||'—','Допуск':ass.industrial_admission||'—','Общая оценка':ass.overall_score??'—','Критических':(ass.severity_summary||{}).critical||0,'Высоких':(ass.severity_summary||{}).high||0})}</div><div class="card"><h3>Методология</h3>${kv({'Режим':ass.mode||'read_only','Метод':ass.methodology||'—','Проверка данных':(ass.data_validation||{}).status||'—'})}</div></div>`)+panel('Оценка по направлениям',table(['Направление','Оценка','Вес','Статус'],dims.map(x=>`<tr><td><b>${esc(x.id)}</b></td><td>${esc(x.score)}%</td><td>${esc(x.weight)}%</td><td>${badge(x.status)}</td></tr>`)),`${dims.length} dimensions`)+panel('Контроли архитектуры',table(['Статус','Контроль','Комментарий'],(ass.architecture_controls||[]).map(x=>`<tr><td>${badge(x.status)}</td><td><b>${esc(x.title)}</b></td><td>${esc(x.note||'')}</td></tr>`)),`${(ass.architecture_controls||[]).length} controls`);'''
        text = text.replace(verification_anchor, assessment_js + verification_anchor, 1)

    text = text.replace(
        "const tc=p.technical_conclusion||{},f=p.findings||[];",
        "const tc=p.technical_conclusion||{},f=bpFindings;",
        1,
    )
    text = text.replace(
        "<div class=\"row\"><span>Статус</span>${badge(tc.status)}</div><div class=\"row\"><span>Подтверждённых отклонений</span><b>${tc.confirmed_findings||0}</b></div>",
        "<div class=\"row\"><span>Вердикт</span>${badge(ass.verdict||tc.status)}</div><div class=\"row\"><span>Допуск к эксплуатации</span><b>${esc(ass.industrial_admission||tc.industrial_admission||'—')}</b></div><div class=\"row\"><span>Общая оценка</span><b>${esc(ass.overall_score??tc.overall_score??'—')}</b></div><div class=\"row\"><span>Подтверждённых отклонений</span><b>${f.length}</b></div>",
        1,
    )
    text = text.replace(
        "table(['Severity','Area','Факт','Действие'],f.map(x=>`<tr><td>${badge(x.severity)}</td><td>${esc(x.area)}</td><td>${esc(x.fact)}</td><td>${esc(x.action)}</td></tr>`))",
        "table(['Severity','Проблема','Факт','Влияние','Исправление'],f.map(x=>`<tr><td>${badge(x.severity)}</td><td><b>${esc(x.title||x.area)}</b></td><td>${esc(x.fact)}</td><td>${esc(x.impact||'')}</td><td>${esc(x.recommendation||x.action||'')}</td></tr>`))",
        1,
    )
    return text


def replace_public_version(text: str) -> str:
    for old in ('4.5.0', '4.4.0', '4.3.3', '4.3.2', '4.3.1', '4.3.0', '3.2.1'):
        text = text.replace(old, '4.6.0')
    return text


def main() -> None:
    AUDIT.write_text(patch_audit(AUDIT.read_text(encoding='utf-8')), encoding='utf-8')
    DASHBOARD.write_text(patch_dashboard(DASHBOARD.read_text(encoding='utf-8')), encoding='utf-8')
    if SOURCE.exists():
        SOURCE.write_text(SOURCE.read_text(encoding='utf-8').replace('VERSION = "4.5.0"', 'VERSION = "4.6.0"'), encoding='utf-8')
    for path in (APP, ADMIN, MANIFEST):
        if path.exists():
            path.write_text(replace_public_version(path.read_text(encoding='utf-8')), encoding='utf-8')
    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8').replace('EDITION = "Active Integration Analysis"', 'EDITION = "Best-Practice Integration Assessment"')
        MANIFEST.write_text(manifest, encoding='utf-8')
    required = {
        AUDIT: ('build_best_practice_assessment(', '"best_practice_assessment"', 'VERSION = "4.6.0"'),
        DASHBOARD: ('AI-BIT Enterprise 4.6.0', 'data-view="assessment"', 'Подтверждённые отклонения'),
    }
    for path, markers in required.items():
        compiled = path.read_text(encoding='utf-8')
        missing = [marker for marker in markers if marker not in compiled]
        if missing:
            raise RuntimeError(f'4.6.0 patch incomplete for {path.name}: {missing}')
    print('Applied AI-BIT Enterprise 4.6.0 — Best-Practice Integration Assessment')


if __name__ == '__main__':
    main()
