from __future__ import annotations

from pathlib import Path

EXEC_PATH = Path('/app/executive_intelligence.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')
REF_PATH = Path('/app/reference_model.py')
CONCLUSION_PATH = Path('/app/management_conclusion.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    executive = EXEC_PATH.read_text(encoding='utf-8')
    executive = once(
        executive,
        'from management_conclusion import build_management_conclusion\n',
        'from management_conclusion import build_management_conclusion\nfrom business_value import build_business_value\n',
        'business value import',
    )
    executive = once(
        executive,
        '"employees_at_risk": int(at_risk)}',
        '"employees_at_risk": int(at_risk), "active_users": int(active_users), "users": int(active_users)}',
        'business value active users source',
    )
    executive = once(
        executive,
        '    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        '    result["business_value"] = build_business_value(result)\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        'business value result',
    )
    executive = executive.replace('2.0.0-alpha.7', '2.0.0-alpha.8')
    EXEC_PATH.write_text(executive, encoding='utf-8')

    conclusion = CONCLUSION_PATH.read_text(encoding='utf-8')
    conclusion = once(
        conclusion,
        '    roi = result.get("roi") or {}\n',
        '    roi = result.get("roi") or {}\n    business_value = result.get("business_value") or {}\n',
        'management conclusion business value source',
    )
    conclusion = once(
        conclusion,
        '''    effect_parts: list[str] = []
    hours = float(roi.get("total_annual_hours") or 0)
    saving = roi.get("total_annual_saving_kzt")
    if hours > 0:
        effect_parts.append(f"до {hours:.0f} рабочих часов в год")
    if saving:
        effect_parts.append(f"ориентировочно {int(saving):,} ₸ в год".replace(",", " "))
''',
        '''    effect_parts: list[str] = []
    labor = business_value.get("labor") or {}
    paper = business_value.get("paper") or {}
    total = business_value.get("total") or {}
    hours = float(labor.get("annual_hours") or roi.get("total_annual_hours") or 0)
    saving = labor.get("annual_saving_kzt") or roi.get("total_annual_saving_kzt")
    hourly_rate = labor.get("hourly_rate_kzt")
    paper_saving = paper.get("annual_saving_kzt")
    total_saving = total.get("annual_saving_kzt")
    if hours > 0:
        effect_parts.append(f"до {hours:.0f} рабочих часов в год")
    if saving:
        rate_note = f" при средней стоимости часа {float(hourly_rate):,.0f} ₸".replace(",", " ") if hourly_rate else ""
        effect_parts.append((f"экономия рабочего времени — ориентировочно {int(saving):,} ₸ в год".replace(",", " ")) + rate_note)
    if paper_saving:
        effect_parts.append(f"экономия на бумаге и печати — ориентировочно {int(paper_saving):,} ₸ в год".replace(",", " "))
    if total_saving:
        effect_parts.append(f"совокупный прогнозируемый эффект — до {int(total_saving):,} ₸ в год".replace(",", " "))
''',
        'management conclusion expected effect',
    )
    conclusion = conclusion.replace('2.0.0-alpha.7', '2.0.0-alpha.8')
    CONCLUSION_PATH.write_text(conclusion, encoding='utf-8')

    dashboard = DASH_PATH.read_text(encoding='utf-8')
    dashboard = once(
        dashboard,
        " const c=d.management_conclusion||{};if(!c.status)return '';\n",
        " const c=d.management_conclusion||{},bv=d.business_value||{},labor=bv.labor||{},paper=bv.paper||{},total=bv.total||{};if(!c.status)return '';\n",
        'dashboard business value vars',
    )

    old_conclusion = '<div class="decision"><b>Ожидаемый эффект</b><span>\'+esc(c.expected_effect||\'требует расчёта\')+\'</span></div>'
    new_conclusion = '<div class="decision"><b>Ожидаемый эффект</b><span>\'+esc(c.expected_effect||\'требует расчёта\')+\'</span>\'+(labor.hourly_rate_kzt?\'<p class="status">Расчёт рабочего времени выполнен по средней стоимости часа \'+money(labor.hourly_rate_kzt)+\'.</p>\':\'\')+(paper.annual_saving_kzt?\'<p><b>Экономия на бумажном документообороте:</b> \'+money(paper.annual_saving_kzt)+\' в год.</p><p class="status">\'+esc(paper.calculation_note||\'Использован усреднённый сценарий AI-BIT.\')+\'</p>\':\'\')+(total.annual_saving_kzt?\'<p><b>Совокупный прогнозируемый эффект:</b> \'+money(total.annual_saving_kzt)+\' в год.</p>\':\'\')+(bv.disclaimer?\'<p class="status">\'+esc(bv.disclaimer)+\'</p>\':\'\')+\'</div>'
    dashboard = once(dashboard, old_conclusion, new_conclusion, 'dashboard business value conclusion')

    old_cards = "<div class=\"roi\"><div class=\"box\"><span>Экономия времени</span><br><strong>'+esc(num(roi.total_annual_hours))+'</strong><br><small>часов в год</small></div><div class=\"box\"><span>Экономический эффект</span><br><strong>'+esc(money(roi.total_annual_saving_kzt))+'</strong><br><small>ориентир в год</small></div></div>"
    new_cards = "<div class=\"roi\"><div class=\"box\"><span>Экономия времени</span><br><strong>'+esc(num(roi.total_annual_hours))+'</strong><br><small>часов в год</small></div><div class=\"box\"><span>Экономия рабочего времени</span><br><strong>'+esc(money(labor.annual_saving_kzt||roi.total_annual_saving_kzt))+'</strong><br><small>'+(labor.hourly_rate_kzt?'при '+money(labor.hourly_rate_kzt)+' за час':'ставка часа не задана')+'</small></div><div class=\"box\"><span>Бумага и печать</span><br><strong>'+esc(money(paper.annual_saving_kzt))+'</strong><br><small>усреднённый прогноз в год</small></div><div class=\"box\"><span>Совокупный эффект</span><br><strong>'+esc(money(total.annual_saving_kzt))+'</strong><br><small>ориентировочно в год</small></div></div>"
    dashboard = once(dashboard, old_cards, new_cards, 'dashboard business value cards')
    DASH_PATH.write_text(dashboard, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH, REF_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.7', '2.0.0-alpha.8')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Business Value Calculator 2.0.0-alpha.8')


if __name__ == '__main__':
    main()
