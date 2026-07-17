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
        'from executive_kpi import build_executive_kpi\n',
        'from executive_kpi import build_executive_kpi\nfrom transformation_intelligence import build_transformation_intelligence\n',
        'transformation intelligence import',
    )
    executive = once(
        executive,
        '    result["executive_kpi"] = build_executive_kpi(result)\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        '    result["executive_kpi"] = build_executive_kpi(result)\n    transformation = build_transformation_intelligence(result, artifacts_dir)\n    result["transformation_roadmap"] = transformation["roadmap"]\n    result["executive_timeline"] = transformation["timeline"]\n    result["risk_forecast"] = transformation["risk_forecast"]\n    result["ai_cio"] = transformation["ai_cio"]\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        'transformation intelligence result',
    )
    executive = executive.replace('2.0.0-alpha.10', '2.0.0-alpha.14')
    EXEC_PATH.write_text(executive, encoding='utf-8')

    dashboard = DASH_PATH.read_text(encoding='utf-8')
    dashboard = once(
        dashboard,
        '.cause-box{padding:10px;border-radius:10px;background:rgba(109,140,255,.07);border:1px solid rgba(109,140,255,.2)}',
        '.cause-box{padding:10px;border-radius:10px;background:rgba(109,140,255,.07);border:1px solid rgba(109,140,255,.2)}.roadmap-phase{margin:12px 0;padding:14px;border-radius:12px;border:1px solid var(--line);background:rgba(16,27,45,.72)}.roadmap-item{padding:10px 0;border-bottom:1px solid rgba(40,57,86,.65)}.roadmap-item:last-child{border-bottom:0}.timeline-row{display:grid;grid-template-columns:150px repeat(4,1fr);gap:8px;padding:8px 0;border-bottom:1px solid rgba(40,57,86,.55)}.forecast-worsening{color:var(--bad)}.forecast-improving{color:var(--ok)}.cio-rank{display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;border-radius:50%;background:rgba(109,140,255,.18);margin-right:8px;font-weight:700}',
        'transformation styles',
    )
    dashboard = once(
        dashboard,
        'function render(d){\n',
        '''function transformationHtml(d){
 const roadmap=d.transformation_roadmap||{},timeline=d.executive_timeline||{},forecast=d.risk_forecast||{},cio=d.ai_cio||{};
 const phases=roadmap.phases||[],points=timeline.points||[],forecasts=forecast.forecasts||[],recs=cio.recommendations||[];
 let out='<section class="section"><h2>Дорожная карта на 90 дней</h2>'+(phases.length?phases.map(p=>'<div class="roadmap-phase"><h3>'+esc(p.title)+' · '+esc(p.period)+'</h3>'+((p.items||[]).length?(p.items||[]).map(x=>'<div class="roadmap-item"><b>'+esc(x.title)+'</b><p>'+esc(x.action||'')+'</p><span class="status">Ответственный: '+esc(x.owner_role||'не назначен')+' · уверенность '+esc(x.confidence||0)+'%</span></div>').join(''):'<div class="empty">На этом этапе действий не сформировано.</div>')+'</div>').join(''):'<div class="empty">Недостаточно данных для дорожной карты.</div>')+'</section>';
 out+='<section class="section"><h2>История изменений</h2>'+(points.length?'<div class="timeline-row"><b>Дата</b><b>Зрелость</b><b>Покрытие</b><b>Просрочка</b><b>Без срока</b></div>'+points.map(x=>'<div class="timeline-row"><span>'+esc(new Date(x.generated_at).toLocaleDateString('ru-RU'))+'</span><span>'+esc(num(x.maturity))+'</span><span>'+esc(num(x.coverage))+'%</span><span>'+esc(num(x.overdue_rate))+'%</span><span>'+esc(x.without_deadline||0)+'</span></div>').join(''):'<div class="empty">Для истории нужен минимум один сохранённый снимок.</div>')+'</section>';
 out+='<section class="section"><h2>Прогноз рисков</h2>'+(forecast.status==='ok'?forecasts.map(x=>'<div class="row"><span>'+esc(x.title)+'<br><small class="status">текущее '+esc(num(x.current))+esc(x.unit||'')+' → прогноз '+esc(num(x.forecast_two_periods))+esc(x.unit||'')+'</small></span><b class="forecast-'+esc(x.direction)+'">'+esc(x.direction==='worsening'?'ухудшение':x.direction==='improving'?'улучшение':'стабильно')+'</b></div>').join(''):'<div class="empty">Для доказательного прогноза требуется минимум 3 снимка. Доступно: '+esc(forecast.available_snapshots||0)+'.</div>')+(forecast.warning?'<p class="status">'+esc(forecast.warning)+'</p>':'')+'</section>';
 out+='<section class="section"><h2>Что бы сделал CIO в ближайшие 90 дней</h2>'+(recs.length?recs.map(x=>'<div class="cause"><h3><span class="cio-rank">'+esc(x.rank)+'</span>'+esc(x.title)+'</h3><p><b>Почему:</b> '+esc(x.why||'')+'</p><div class="decision"><b>Решение</b><span>'+esc(x.decision||'')+'</span></div><span class="status">Срок: '+esc(x.period||'')+' · '+esc(x.owner_role||'')+' · уверенность '+esc(x.confidence||0)+'%</span></div>').join(''):'<div class="empty">Приоритетные действия не сформированы.</div>')+'<p class="status">'+esc(cio.principle||'')+'</p></section>';
 return out;
}
function render(d){
''',
        'transformation renderer',
    )
    dashboard = once(
        dashboard,
        " let html=conclusionHtml(d)+executiveKpiHtml(d)+'<div class=\"summary\">",
        " let html=conclusionHtml(d)+executiveKpiHtml(d)+transformationHtml(d)+'<div class=\"summary\">",
        'transformation placement',
    )
    dashboard = dashboard.replace('2.0.0-alpha.10', '2.0.0-alpha.14')
    DASH_PATH.write_text(dashboard, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH, REF_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.10', '2.0.0-alpha.14')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Roadmap Generator 2.0.0-alpha.11')
    print('Applied AI-BIT Executive Timeline 2.0.0-alpha.12')
    print('Applied AI-BIT Evidence-Based Risk Forecast 2.0.0-alpha.13')
    print('Applied AI-BIT AI CIO 2.0.0-alpha.14')


if __name__ == '__main__':
    main()
