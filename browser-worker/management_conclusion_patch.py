from __future__ import annotations

from pathlib import Path

EXEC_PATH = Path('/app/executive_intelligence.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')
REF_PATH = Path('/app/reference_model.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    executive = EXEC_PATH.read_text(encoding='utf-8')
    executive = once(
        executive,
        'from reference_model import build_reference_audit\n',
        'from reference_model import build_reference_audit\nfrom management_conclusion import build_management_conclusion\n',
        'management conclusion import',
    )
    executive = once(
        executive,
        '    root = artifacts_dir / "executive-intelligence"\n',
        '    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n    root = artifacts_dir / "executive-intelligence"\n',
        'management conclusion result',
    )
    executive = executive.replace('2.0.0-alpha.6', '2.0.0-alpha.7')
    EXEC_PATH.write_text(executive, encoding='utf-8')

    dashboard = DASH_PATH.read_text(encoding='utf-8')
    dashboard = once(
        dashboard,
        '.notice{padding:10px 12px;border:1px solid rgba(255,189,74,.35);background:rgba(255,189,74,.08);border-radius:10px;margin-bottom:12px}',
        '.notice{padding:10px 12px;border:1px solid rgba(255,189,74,.35);background:rgba(255,189,74,.08);border-radius:10px;margin-bottom:12px}.conclusion{border:1px solid rgba(109,140,255,.4);background:linear-gradient(135deg,rgba(109,140,255,.12),rgba(16,27,45,.96));}.conclusion h2{font-size:21px}.conclusion-lead{font-size:16px;line-height:1.65;margin:0 0 14px}.conclusion-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}.conclusion ul{margin:8px 0 0;padding-left:20px}.conclusion li{margin:7px 0}.conclusion-callout{padding:13px;border-radius:11px;background:rgba(255,93,120,.08);border:1px solid rgba(255,93,120,.24)}',
        'management conclusion styles',
    )
    dashboard = once(
        dashboard,
        'function render(d){\n',
        '''function conclusionHtml(d){
 const c=d.management_conclusion||{};if(!c.status)return '';
 const findings=c.findings||[],actions=c.required_actions||[],risks=c.inaction_risks||[],timeline=c.timeline||{};
 let timelineText='';if(timeline.first_activity_at){timelineText='Первые подтверждённые рабочие данные: '+new Date(timeline.first_activity_at).toLocaleDateString('ru-RU')+(timeline.age_days!=null?' · наблюдаемый период '+timeline.age_days+' дней':'');}
 return '<section class="section conclusion"><h2>Заключение AI-BIT</h2><p class="conclusion-lead">'+esc(c.status)+'</p><p><b>Общий вывод:</b> '+esc(c.summary||'')+'</p>'+(timelineText?'<p class="status">'+esc(timelineText)+'</p>':'')+'<div class="conclusion-grid"><div><h3>Что показывает анализ</h3>'+(findings.length?'<ul>'+findings.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':'<p class="empty">Недостаточно данных для выводов.</p>')+'<h3>Что необходимо сделать</h3>'+(actions.length?'<ol>'+actions.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ol>':'<p class="empty">Отдельных действий не требуется.</p>')+'</div><div><div class="conclusion-callout"><b>Если ничего не менять</b>'+(risks.length?'<ul>'+risks.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':'<p>Существенных рисков бездействия не выявлено.</p>')+'</div><div class="decision"><b>Ожидаемый эффект</b><span>'+esc(c.expected_effect||'требует расчёта')+'</span></div></div></div></section>';
}
function render(d){
''',
        'management conclusion renderer',
    )
    dashboard = once(
        dashboard,
        " let html='<div class=\"summary\">",
        " let html=conclusionHtml(d)+'<div class=\"summary\">",
        'management conclusion placement',
    )
    DASH_PATH.write_text(dashboard, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH, REF_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.6', '2.0.0-alpha.7')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Management Conclusion 2.0.0-alpha.7')


if __name__ == '__main__':
    main()
