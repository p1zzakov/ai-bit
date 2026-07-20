from __future__ import annotations

from pathlib import Path

MANAGEMENT_PATH = Path('/app/management_report.py')
APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    text = MANAGEMENT_PATH.read_text(encoding='utf-8')
    text = text.replace('VERSION = "1.0.0-rc.12"', 'VERSION = "1.0.0-rc.13"')

    helper_marker = '''def render_html(report: dict[str, Any]) -> str:\n'''
    helper = '''def _executive_intelligence_html(report: dict[str, Any]) -> str:\n    intelligence = report.get("executive_intelligence_snapshot") or {}\n    maturity = intelligence.get("digital_maturity") or {}\n    dimensions = intelligence.get("dimensions") or {}\n    risks = intelligence.get("risks") or []\n    departments = intelligence.get("department_rating") or []\n    roi = intelligence.get("roi") or {}\n\n    if not intelligence:\n        return '<section><h2>Паспорт цифровой зрелости</h2><p class="muted">Данные Executive Intelligence отсутствуют.</p></section>'\n\n    score = maturity.get("score", "—")\n    grade = maturity.get("grade", "—")\n    level = maturity.get("level", "Недостаточно данных")\n\n    dimension_cards = "".join(\n        '<div class="metric"><div class="metric-name">' + escape(str(item.get("title", key))) + '</div>'\n        + '<div class="metric-score">' + escape(str(item.get("score", "—"))) + '/100</div>'\n        + '<div class="metric-grade">' + escape(str(item.get("grade", "—"))) + '</div></div>'\n        for key, item in dimensions.items()\n    ) or '<p class="muted">Оценки направлений отсутствуют.</p>'\n\n    risk_items = [\n        f'{row.get("title", "Риск")}: {row.get("fact", "")}. Возможное последствие: {row.get("impact", "")}'\n        for row in risks[:7]\n    ]\n    department_items = [\n        f'{row.get("name", "Подразделение")}: {row.get("score", "—")}/100, рейтинг {row.get("grade", "—")}'\n        for row in departments[:7]\n    ]\n\n    annual_hours = roi.get("total_annual_hours")\n    annual_saving = roi.get("total_annual_saving_kzt")\n    roi_text = 'Потенциальная экономия времени: данных недостаточно.'\n    if annual_hours is not None:\n        roi_text = f'Потенциальная экономия времени: до {annual_hours} часов в год.'\n    if annual_saving is not None:\n        roi_text += f' Ориентировочный экономический эффект: до {annual_saving:,.0f} тенге в год.'.replace(',', ' ')\n\n    return (\n        '<section><h2>Паспорт цифровой зрелости</h2>'\n        f'<div class="maturity"><div class="maturity-score">{escape(str(score))}</div>'\n        f'<div><b>Уровень: {escape(str(level))}</b><br><span class="muted">Рейтинг {escape(str(grade))}</span></div></div>'\n        f'<div class="metrics">{dimension_cards}</div></section>'\n        '<section><h2>Ключевые управленческие риски</h2>' + _render_list(risk_items) + '</section>'\n        '<section><h2>Подразделения, требующие внимания</h2>' + _render_list(department_items) + '</section>'\n        f'<section><h2>Потенциал автоматизации и экономический эффект</h2><p>{escape(roi_text)}</p></section>'\n    )\n\n\n''' + helper_marker
    text = once(text, helper_marker, helper, 'executive intelligence html helper')

    style_marker = '''.lead{{font-size:17px;background:#f4f7ff;border-left:5px solid #5876e8;padding:18px;border-radius:8px}}.muted{{color:#68758c}}'''
    style_replacement = '''.lead{{font-size:17px;background:#f4f7ff;border-left:5px solid #5876e8;padding:18px;border-radius:8px}}.muted{{color:#68758c}}.maturity{{display:flex;align-items:center;gap:18px;padding:18px;border-radius:12px;background:#eef3ff;border:1px solid #cfdbff;margin:12px 0}}.maturity-score{{font-size:42px;font-weight:800;color:#3859c7}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}}.metric{{padding:12px;border:1px solid #dce3f0;border-radius:9px;background:#f8faff}}.metric-name{{font-size:12px;color:#68758c}}.metric-score{{font-size:20px;font-weight:700;margin-top:4px}}.metric-grade{{font-size:12px;color:#3859c7}}'''
    text = once(text, style_marker, style_replacement, 'management report intelligence styles')

    html_marker = '''<section><h2>Цифровая зрелость</h2><p>{escape(str(report.get("digital_maturity_summary", "Данных для оценки недостаточно.")))}</p></section>'''
    html_replacement = html_marker + '''\n{_executive_intelligence_html(report)}'''
    text = once(text, html_marker, html_replacement, 'deterministic executive intelligence report section')

    report_marker = '''    report = json.loads(content)\n    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")'''
    report_replacement = '''    report = json.loads(content)\n    # Store the factual Executive Intelligence snapshot in every report.\n    # Its dedicated HTML section is rendered deterministically and therefore\n    # does not depend on whether Groq chooses to mention every metric.\n    report["executive_intelligence_snapshot"] = context.get("executive_intelligence", {})\n    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")'''
    text = once(text, report_marker, report_replacement, 'persist executive intelligence snapshot')

    MANAGEMENT_PATH.write_text(text, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH):
        runtime = path.read_text(encoding='utf-8')
        runtime = runtime.replace('1.0.0-rc.12', '1.0.0-rc.13')
        path.write_text(runtime, encoding='utf-8')

    print('Applied AI-BIT deterministic management intelligence report patch 1.0.0-rc.13')


if __name__ == '__main__':
    main()
