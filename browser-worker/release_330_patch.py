from __future__ import annotations

from pathlib import Path

VERSION = "3.3.0"
EXEC_PATH = Path('/app/executive_intelligence.py')
INTEL_DASH_PATH = Path('/app/executive_intelligence_dashboard.py')
MANAGEMENT_PATH = Path('/app/management_compact.py')
VERSION_PATHS = [
    Path('/app/app.py'),
    Path('/app/admin_dashboard.py'),
    Path('/app/reference_model.py'),
    Path('/app/executive_intelligence.py'),
    Path('/app/process_optimizer.py'),
]


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    executive = EXEC_PATH.read_text(encoding='utf-8')
    if 'from executive_decision_intelligence import enrich_executive_decision_intelligence' not in executive:
        executive = once(
            executive,
            'from process_optimizer import build_process_optimizer\n',
            'from process_optimizer import build_process_optimizer\nfrom executive_decision_intelligence import enrich_executive_decision_intelligence\n',
            'decision intelligence import',
        )
    if 'enrich_executive_decision_intelligence(result)' not in executive:
        executive = once(
            executive,
            '    result["process_optimizer"] = build_process_optimizer(result, artifacts_dir)\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
            '    result["process_optimizer"] = build_process_optimizer(result, artifacts_dir)\n    result = enrich_executive_decision_intelligence(result)\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
            'decision intelligence enrichment',
        )
    EXEC_PATH.write_text(executive, encoding='utf-8')

    dashboard = INTEL_DASH_PATH.read_text(encoding='utf-8')
    marker = 'ai-bit-executive-decision-330'
    if marker not in dashboard:
        css = r'''
/* ai-bit-executive-decision-330 */
.executive-score-card{display:grid;grid-template-columns:170px minmax(0,1fr);gap:20px;align-items:center}.executive-score-value{font-size:56px;font-weight:760;letter-spacing:-.055em;line-height:1}.executive-score-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.chip{display:inline-flex;padding:5px 9px;border-radius:999px;background:#f1f2f4;color:#555961;font-size:12px}.decision-list{display:grid;gap:10px}.decision-item{padding:14px;border:1px solid var(--line);border-radius:11px;background:#fff}.decision-rank{display:inline-grid;width:26px;height:26px;place-items:center;border-radius:8px;background:#eef0ff;color:#525cc7;font-weight:700;margin-right:8px}.department-row{display:grid;grid-template-columns:minmax(170px,1fr) 120px 52px;gap:12px;align-items:center;padding:11px 0;border-bottom:1px solid #eff0f2}.department-row:last-child{border-bottom:0}.timeline-highlights{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.timeline-highlight{padding:13px;border:1px solid var(--line);border-radius:10px;background:#fbfbfc}.timeline-highlight strong{display:block;font-size:22px;margin-top:6px}.improved{color:var(--ok)}.worsened{color:var(--bad)}.stable{color:var(--muted)}@media(max-width:850px){.executive-score-card{grid-template-columns:1fr}.timeline-highlights{grid-template-columns:repeat(2,1fr)}.department-row{grid-template-columns:1fr 90px 42px}}@media(max-width:560px){.timeline-highlights{grid-template-columns:1fr}}
'''
        dashboard = dashboard.replace('</style>', css + '</style>', 1)
        dashboard = once(
            dashboard,
            'function rows(list,render,empty=\'Данных пока нет\'){return list&&list.length?list.map(render).join(\'\'):`<div class="empty">${empty}</div>`}\n',
            '''function rows(list,render,empty='Данных пока нет'){return list&&list.length?list.map(render).join(''):`<div class="empty">${empty}</div>`}
function executiveDecisionHtml(d){
 const score=d.executive_score||{},dept=d.department_maturity||{},timeline=d.ai_timeline||{},cio=d.ai_cio||{};
 const components=score.components||[],departments=dept.departments||[],highlights=timeline.highlights||[],recommendations=cio.recommendations||[];
 let html='<section class="card section executive-score-card" style="margin-top:18px"><div><div class="muted">AI-BIT Executive Score</div><div class="executive-score-value">'+esc(score.score||0)+'</div><div class="muted">из 100 · '+esc(score.grade||'—')+'</div></div><div><h2>Единый управленческий индекс</h2><div class="muted">До целевого уровня '+esc(score.target||80)+': '+esc(score.gap_to_target||0)+' баллов. Покрытие расчёта: '+esc(score.coverage_percent||0)+'%.</div><div class="executive-score-meta">'+components.map(x=>'<span class="chip">'+esc(x.title)+': '+esc(x.score)+'</span>').join('')+'</div><div class="detail" style="margin-top:12px">'+esc(score.methodology||'')+'</div></div></section>';
 html+='<section class="grid"><div class="card section"><h2>Рекомендации AI CIO</h2><div class="decision-list">'+(recommendations.length?recommendations.map(x=>'<div class="decision-item"><div class="title"><span class="decision-rank">'+esc(x.rank)+'</span>'+esc(x.title)+'</div><div class="detail"><b>Основание:</b> '+esc(x.why||'')+'</div><div class="detail"><b>Решение:</b> '+esc(x.decision||'')+'</div><div class="detail">'+esc(x.period||'')+' · '+esc(x.owner_role||'')+' · уверенность '+esc(x.confidence||0)+'%</div></div>').join(''):'<div class="empty">Подтверждённые рекомендации пока не сформированы.</div>')+'</div><div class="detail" style="margin-top:12px">'+esc(cio.principle||'')+'</div></div>';
 html+='<div class="card section"><h2>Зрелость подразделений</h2>'+(dept.status==='ok'?departments.slice(0,20).map(x=>'<div class="department-row"><div><b>'+esc(x.name)+'</b><div class="detail">Просрочка '+esc(x.overdue_rate)+'% · открыто '+esc(x.open_tasks)+'</div></div><div class="bar"><span style="width:'+Number(x.score||0)+'%"></span></div><div class="grade">'+esc(x.grade)+'</div></div>').join(''):'<div class="empty">Недостаточно данных по подразделениям.</div>')+'<div class="detail" style="margin-top:12px">'+esc(dept.methodology||'')+'</div></div></section>';
 html+='<section class="card section" style="margin-top:18px"><h2>AI Timeline</h2>'+(timeline.status==='ok'?'<div class="timeline-highlights">'+highlights.map(x=>'<div class="timeline-highlight"><div class="muted">'+esc(x.title)+'</div><strong class="'+esc(x.direction)+'">'+(Number(x.delta)>0?'+':'')+esc(x.delta)+esc(x.suffix||'')+'</strong></div>').join('')+'</div>':'<div class="empty">Для динамики требуется минимум два сохранённых снимка. Доступно: '+esc(timeline.available_snapshots||0)+'.</div>')+'<div class="detail" style="margin-top:12px">'+esc(timeline.methodology||'')+'</div></section>';
 return html;
}
''',
            'decision intelligence renderer',
        )
        dashboard = once(
            dashboard,
            'function render(d){const m=d.digital_maturity||{},dims=Object.values(d.dimensions||{}),roi=d.roi||{},road=d.roadmap||{};document.querySelector(\'#app\').innerHTML=`',
            'function render(d){const m=d.digital_maturity||{},dims=Object.values(d.dimensions||{}),roi=d.roi||{},road=d.roadmap||{};document.querySelector(\'#app\').innerHTML=executiveDecisionHtml(d)+`',
            'decision intelligence dashboard placement',
        )
        INTEL_DASH_PATH.write_text(dashboard, encoding='utf-8')

    management = MANAGEMENT_PATH.read_text(encoding='utf-8')
    management = management.replace('const m=d.digital_maturity||{},s=d.source_summary||{}', 'const m=d.executive_score||d.digital_maturity||{},s=d.source_summary||{}')
    management = management.replace('Общая оценка внедрения', 'Executive Score')
    management = management.replace("esc(m.level||'')", "esc(m.grade||m.level||'')")
    MANAGEMENT_PATH.write_text(management, encoding='utf-8')

    for path in VERSION_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8').replace('3.2.1', VERSION)
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Enterprise 3.3.0 — Evidence-Based Executive Decision Intelligence')


if __name__ == '__main__':
    main()
