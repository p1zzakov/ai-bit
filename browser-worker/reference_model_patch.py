from __future__ import annotations

from pathlib import Path

EXEC_PATH = Path('/app/executive_intelligence.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    text = EXEC_PATH.read_text(encoding='utf-8')
    text = once(
        text,
        'from typing import Any\n',
        'from typing import Any\n\nfrom reference_model import build_reference_audit\n',
        'reference model import',
    )
    text = once(
        text,
        '    process_mining = _latest(artifacts_dir, "process-mining")\n',
        '    process_mining = _latest(artifacts_dir, "process-mining")\n    reference_audit = build_reference_audit(artifacts_dir)\n',
        'reference audit build',
    )
    text = once(
        text,
        '    maturity = _clamp(sum(item["score"] for item in dimensions.values()) / len(dimensions))\n',
        '    maturity = _clamp(sum(item["score"] for item in dimensions.values()) / len(dimensions))\n    reference_coverage = _num(reference_audit.get("coverage"), 0)\n    maturity = _clamp(maturity * 0.75 + reference_coverage * 0.25)\n',
        'reference coverage maturity',
    )
    text = once(
        text,
        '    risks: list[dict[str, Any]] = []\n',
        '''    risks: list[dict[str, Any]] = []
    reference_missing = (reference_audit.get("summary") or {}).get("missing", 0)
    reference_unknown = (reference_audit.get("summary") or {}).get("unknown", 0)
    if reference_missing:
        risks.append({
            "severity": "critical",
            "title": "Внедрение не соответствует целевой модели",
            "fact": f"Не реализовано {reference_missing} обязательных возможностей из эталонной модели; ещё {reference_unknown} требуют проверки",
            "impact": "Компания использует только часть возможностей Bitrix24, ключевые процессы остаются ручными или находятся вне единого контура",
            "priority": 120,
        })
''',
        'reference model risk',
    )
    text = once(
        text,
        '        "source_summary": {"implementation_score": implementation, "enterprise_health": enterprise_health, "overdue_rate": overdue_rate, "without_deadline": int(without_deadline), "employees_at_risk": int(at_risk)},\n',
        '        "source_summary": {"implementation_score": implementation, "enterprise_health": enterprise_health, "overdue_rate": overdue_rate, "without_deadline": int(without_deadline), "employees_at_risk": int(at_risk)},\n        "reference_audit": reference_audit,\n',
        'reference audit result',
    )
    EXEC_PATH.write_text(text, encoding='utf-8')

    dash = DASH_PATH.read_text(encoding='utf-8')
    dash = once(
        dash,
        "function render(d){const maturity=d.digital_maturity||{},src=d.source_summary||{},roi=d.roi||{},risks=(d.risks||[]).slice(0,5),deps=(d.department_rating||[]).slice(0,5),dims=Object.values(d.dimensions||{}),dec=decisions(d);",
        "function render(d){const maturity=d.digital_maturity||{},src=d.source_summary||{},roi=d.roi||{},risks=(d.risks||[]).slice(0,5),deps=(d.department_rating||[]).slice(0,5),dims=Object.values(d.dimensions||{}),dec=decisions(d),ref=d.reference_audit||{},refSummary=ref.summary||{},refGaps=(ref.critical_gaps||[]).slice(0,8);",
        'dashboard reference vars',
    )
    dash = once(
        dash,
        "const gaps=d.missing_capabilities||[];html+='<section class=\"section\"><h2>Ключевые процессы, которые не внедрены</h2>",
        "html+='<section class=\"section\"><h2>Сравнение с эталонной моделью</h2><div class=\"summary\" style=\"grid-template-columns:1fr 1fr 1fr 1fr\"><div class=\"card metric\"><div class=\"label\">Профиль</div><div class=\"value\" style=\"font-size:18px\">'+esc((ref.profile||{}).title||'Не выбран')+'</div></div><div class=\"card metric\"><div class=\"label\">Покрытие эталона</div><div class=\"value '+(Number(ref.coverage)<50?'bad':Number(ref.coverage)<75?'warn':'ok')+'\">'+esc(num(ref.coverage))+'%</div></div><div class=\"card metric\"><div class=\"label\">Не реализовано</div><div class=\"value bad\">'+esc(refSummary.missing||0)+'</div></div><div class=\"card metric\"><div class=\"label\">Требует проверки</div><div class=\"value warn\">'+esc(refSummary.unknown||0)+'</div></div></div>'+(refGaps.length?refGaps.map((x,i)=>'<div class=\"issue\"><div class=\"rank\">'+(i+1)+'</div><div><h3>'+esc(x.title)+'</h3><p><b class=\"bad\">Не реализовано</b> · '+esc(x.domain||'')+'</p></div></div>').join(''):'<div class=\"empty\">Критичных разрывов по эталонной модели не найдено.</div>')+'</section>';const gaps=d.missing_capabilities||[];html+='<section class=\"section\"><h2>Ключевые процессы, которые не внедрены</h2>",
        'dashboard reference section',
    )
    DASH_PATH.write_text(dash, encoding='utf-8')

    app = APP_PATH.read_text(encoding='utf-8')
    app = once(
        app,
        'from executive_intelligence import build_executive_intelligence, read_latest_executive_intelligence',
        'from executive_intelligence import build_executive_intelligence, read_latest_executive_intelligence\nfrom reference_model import build_reference_audit, load_reference_model, read_latest_reference_audit',
        'app reference imports',
    )
    marker = '''@app.get("/executive-intelligence/latest")
async def executive_intelligence_latest() -> dict[str, Any]:
    try:
        return read_latest_executive_intelligence(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return build_executive_intelligence(settings.browser_artifacts_dir)
'''
    addition = marker + '''

@app.get("/reference-model")
async def reference_model_get() -> dict[str, Any]:
    return load_reference_model()


@app.post("/reference-audit/collect")
async def reference_audit_collect(profile: str | None = None) -> dict[str, Any]:
    return build_reference_audit(settings.browser_artifacts_dir, profile=profile)


@app.get("/reference-audit/latest")
async def reference_audit_latest() -> dict[str, Any]:
    try:
        return read_latest_reference_audit(settings.browser_artifacts_dir)
    except FileNotFoundError:
        return build_reference_audit(settings.browser_artifacts_dir)
'''
    app = once(app, marker, addition, 'reference model endpoints')
    app = app.replace('1.0.0-rc.15', '2.0.0-alpha.1')
    APP_PATH.write_text(app, encoding='utf-8')

    admin = ADMIN_PATH.read_text(encoding='utf-8').replace('1.0.0-rc.15', '2.0.0-alpha.1')
    ADMIN_PATH.write_text(admin, encoding='utf-8')
    print('Applied AI-BIT Reference Model Audit 2.0.0-alpha.1')


if __name__ == '__main__':
    main()
