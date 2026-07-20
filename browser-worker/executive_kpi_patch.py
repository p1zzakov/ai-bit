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
        'from business_value import build_business_value\n',
        'from business_value import build_business_value\nfrom executive_kpi import build_executive_kpi\n',
        'executive KPI import',
    )
    executive = once(
        executive,
        '    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        '    result["executive_kpi"] = build_executive_kpi(result)\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        'executive KPI result',
    )
    executive = executive.replace('2.0.0-alpha.9', '2.0.0-alpha.10')
    EXEC_PATH.write_text(executive, encoding='utf-8')

    dashboard = DASH_PATH.read_text(encoding='utf-8')
    dashboard = once(
        dashboard,
        '.conclusion-callout{padding:13px;border-radius:11px;background:rgba(255,93,120,.08);border:1px solid rgba(255,93,120,.24)}',
        '.conclusion-callout{padding:13px;border-radius:11px;background:rgba(255,93,120,.08);border:1px solid rgba(255,93,120,.24)}.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.kpi-card{padding:14px;border-radius:12px;background:rgba(16,27,45,.82);border:1px solid var(--line)}.kpi-card strong{display:block;font-size:27px;margin:5px 0}.kpi-good strong{color:var(--ok)}.kpi-attention strong{color:var(--warn)}.kpi-critical strong{color:var(--bad)}.cause{padding:14px 0;border-bottom:1px solid rgba(40,57,86,.75)}.cause:last-child{border-bottom:0}.cause-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}.cause-box{padding:10px;border-radius:10px;background:rgba(109,140,255,.07);border:1px solid rgba(109,140,255,.2)}@media(max-width:1050px){.kpi-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.kpi-grid{grid-template-columns:1fr}.cause-grid{grid-template-columns:1fr}}',
        'executive KPI styles',
    )
    dashboard = once(
        dashboard,
        'function render(d){\n',
        '''function executiveKpiHtml(d){
 const center=d.executive_kpi||{},kpis=center.kpis||[],causes=center.root_causes||[];
 if(!kpis.length)return '';
 return '<section class="section"><h2>Ключевые показатели руководителя</h2><div class="kpi-grid">'+kpis.map(x=>'<div class="kpi-card kpi-'+esc(x.level||'attention')+'"><span class="status">'+esc(x.title)+'</span><strong>'+esc(num(x.score))+'</strong><small>'+esc(x.explanation||'')+'</small></div>').join('')+'</div></section>'+
 '<section class="section"><h2>Почему возникают проблемы</h2>'+(causes.length?causes.map((x,i)=>'<div class="cause"><h3>'+(i+1)+'. '+esc(x.title)+'</h3><p><b>Факт:</b> '+esc(x.fact||'')+'</p><div class="cause-grid"><div class="cause-box"><b>Корневая причина</b><br>'+esc(x.root_cause||'')+'</div><div class="cause-box"><b>Влияние на бизнес</b><br>'+esc(x.business_impact||'')+'</div></div><div class="decision"><b>Что сделать</b><span>'+esc(x.recommended_action||'')+'</span></div><span class="status">Уверенность вывода: '+esc(x.confidence||0)+'%</span></div>').join(''):'<div class="empty">Существенных причин отклонений не выявлено.</div>')+'</section>';
}
function render(d){
''',
        'executive KPI renderer',
    )
    dashboard = once(
        dashboard,
        " let html=conclusionHtml(d)+'<div class=\"summary\">",
        " let html=conclusionHtml(d)+executiveKpiHtml(d)+'<div class=\"summary\">",
        'executive KPI placement',
    )
    dashboard = dashboard.replace('2.0.0-alpha.9', '2.0.0-alpha.10')
    DASH_PATH.write_text(dashboard, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH, REF_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.9', '2.0.0-alpha.10')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Executive KPI Center + Root Cause Analysis 2.0.0-alpha.10')


if __name__ == '__main__':
    main()
