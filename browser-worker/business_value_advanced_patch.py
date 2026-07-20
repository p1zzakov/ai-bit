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
        '"employees_at_risk": int(at_risk), "active_users": int(active_users), "users": int(active_users)}',
        '"employees_at_risk": int(at_risk), "active_users": int(active_users), "users": int(active_users), "open": int(open_tasks), "overdue": int(round(open_tasks * overdue_rate / 100))}',
        'advanced value operational source',
    )
    executive = executive.replace('2.0.0-alpha.8', '2.0.0-alpha.9')
    EXEC_PATH.write_text(executive, encoding='utf-8')

    conclusion = CONCLUSION_PATH.read_text(encoding='utf-8')
    conclusion = once(
        conclusion,
        '    total = business_value.get("total") or {}\n',
        '    total = business_value.get("total") or {}\n    overdue_value = business_value.get("overdue_losses") or {}\n    no_deadline_value = business_value.get("no_deadline_losses") or {}\n    management_value = business_value.get("management_time") or {}\n    search_value = business_value.get("document_search") or {}\n',
        'advanced value conclusion sources',
    )
    conclusion = once(
        conclusion,
        '    if total_saving:\n        effect_parts.append(f"совокупный прогнозируемый эффект — до {int(total_saving):,} ₸ в год".replace(",", " "))\n',
        '    if overdue_value.get("annual_loss_kzt"):\n        effect_parts.append(f"потенциал снижения потерь от просрочки — до {int(overdue_value[\"annual_loss_kzt\"]):,} ₸ в год".replace(",", " "))\n    if no_deadline_value.get("annual_loss_kzt"):\n        effect_parts.append(f"потенциал снижения потерь по задачам без срока — до {int(no_deadline_value[\"annual_loss_kzt\"]):,} ₸ в год".replace(",", " "))\n    if management_value.get("annual_saving_kzt"):\n        effect_parts.append(f"экономия времени руководителей — до {int(management_value[\"annual_saving_kzt\"]):,} ₸ в год".replace(",", " "))\n    if search_value.get("annual_saving_kzt"):\n        effect_parts.append(f"экономия на поиске документов — до {int(search_value[\"annual_saving_kzt\"]):,} ₸ в год".replace(",", " "))\n    if total_saving:\n        effect_parts.append(f"совокупный прогнозируемый эффект — до {int(total_saving):,} ₸ в год".replace(",", " "))\n',
        'advanced value conclusion effects',
    )
    conclusion = conclusion.replace('2.0.0-alpha.8', '2.0.0-alpha.9')
    CONCLUSION_PATH.write_text(conclusion, encoding='utf-8')

    dashboard = DASH_PATH.read_text(encoding='utf-8')
    dashboard = once(
        dashboard,
        " const c=d.management_conclusion||{},bv=d.business_value||{},labor=bv.labor||{},paper=bv.paper||{},total=bv.total||{};if(!c.status)return '';\n",
        " const c=d.management_conclusion||{},bv=d.business_value||{},labor=bv.labor||{},paper=bv.paper||{},total=bv.total||{},overdueValue=bv.overdue_losses||{},deadlineValue=bv.no_deadline_losses||{},managementValue=bv.management_time||{},searchValue=bv.document_search||{},approvals=bv.approvals||{},unused=bv.unused_potential||{};if(!c.status)return '';\n",
        'advanced value dashboard vars',
    )
    dashboard = once(
        dashboard,
        " const maturity=d.digital_maturity||{},src=d.source_summary||{},roi=d.roi||{},risks=(d.risks||[]).slice(0,5),deps=(d.department_rating||[]).filter(x=>Number(x.open||0)>=3||Number(x.score||0)<70).slice(0,5),dims=Object.values(d.dimensions||{}),dec=decisions(d),ref=d.reference_audit||{},refSummary=ref.summary||{},refGaps=(ref.critical_gaps||[]).filter(x=>x.required!==false).slice(0,6);\n",
        " const maturity=d.digital_maturity||{},src=d.source_summary||{},roi=d.roi||{},bv=d.business_value||{},labor=bv.labor||{},paper=bv.paper||{},total=bv.total||{},overdueValue=bv.overdue_losses||{},deadlineValue=bv.no_deadline_losses||{},managementValue=bv.management_time||{},searchValue=bv.document_search||{},approvals=bv.approvals||{},unused=bv.unused_potential||{},risks=(d.risks||[]).slice(0,5),deps=(d.department_rating||[]).filter(x=>Number(x.open||0)>=3||Number(x.score||0)<70).slice(0,5),dims=Object.values(d.dimensions||{}),dec=decisions(d),ref=d.reference_audit||{},refSummary=ref.summary||{},refGaps=(ref.critical_gaps||[]).filter(x=>x.required!==false).slice(0,6);\n",
        'advanced value render vars',
    )
    old_cards = "<div class=\"roi\"><div class=\"box\"><span>Экономия времени</span><br><strong>'+esc(num(roi.total_annual_hours))+'</strong><br><small>часов в год</small></div><div class=\"box\"><span>Экономия рабочего времени</span><br><strong>'+esc(money(labor.annual_saving_kzt||roi.total_annual_saving_kzt))+'</strong><br><small>'+(labor.hourly_rate_kzt?'при '+money(labor.hourly_rate_kzt)+' за час':'ставка часа не задана')+'</small></div><div class=\"box\"><span>Бумага и печать</span><br><strong>'+esc(money(paper.annual_saving_kzt))+'</strong><br><small>усреднённый прогноз в год</small></div><div class=\"box\"><span>Совокупный эффект</span><br><strong>'+esc(money(total.annual_saving_kzt))+'</strong><br><small>ориентировочно в год</small></div></div>"
    new_cards = "<div class=\"roi\"><div class=\"box\"><span>Автоматизация операций</span><br><strong>'+esc(money(labor.annual_saving_kzt||roi.total_annual_saving_kzt))+'</strong><br><small>'+(labor.hourly_rate_kzt?'при '+money(labor.hourly_rate_kzt)+' за час':'ставка часа не задана')+'</small></div><div class=\"box\"><span>Бумага и печать</span><br><strong>'+esc(money(paper.annual_saving_kzt))+'</strong><br><small>усреднённый прогноз</small></div><div class=\"box\"><span>Потери от просрочки</span><br><strong>'+esc(money(overdueValue.annual_loss_kzt))+'</strong><br><small>'+esc(num(overdueValue.annual_hours))+' часов в год</small></div><div class=\"box\"><span>Задачи без срока</span><br><strong>'+esc(money(deadlineValue.annual_loss_kzt))+'</strong><br><small>'+esc(num(deadlineValue.annual_hours))+' часов контроля</small></div><div class=\"box\"><span>Время руководителей</span><br><strong>'+esc(money(managementValue.annual_saving_kzt))+'</strong><br><small>'+esc(num(managementValue.annual_hours))+' часов в год</small></div><div class=\"box\"><span>Поиск документов</span><br><strong>'+esc(money(searchValue.annual_saving_kzt))+'</strong><br><small>'+esc(num(searchValue.annual_hours))+' часов в год</small></div><div class=\"box\"><span>Неиспользуемый потенциал</span><br><strong>'+esc(money(unused.indicative_value_kzt))+'</strong><br><small>индикатор, не включён в итог</small></div><div class=\"box\"><span>Совокупный эффект</span><br><strong>'+esc(money(total.annual_saving_kzt))+'</strong><br><small>'+esc(num(total.annual_hours))+' часов в год</small></div></div><p class=\"status\">'+esc((approvals.calculation_note||''))+' '+esc((total.calculation_note||''))+'</p>"
    dashboard = once(dashboard, old_cards, new_cards, 'advanced value dashboard cards')
    dashboard = dashboard.replace('2.0.0-alpha.8', '2.0.0-alpha.9')
    DASH_PATH.write_text(dashboard, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH, REF_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.8', '2.0.0-alpha.9')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Advanced Business Value Engine 2.0.0-alpha.9')


if __name__ == '__main__':
    main()
