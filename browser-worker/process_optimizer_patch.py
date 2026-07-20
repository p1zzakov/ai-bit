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
        'from transformation_intelligence import build_transformation_intelligence\n',
        'from transformation_intelligence import build_transformation_intelligence\nfrom process_optimizer import build_process_optimizer\n',
        'process optimizer import',
    )
    executive = once(
        executive,
        '    result["ai_cio"] = transformation["ai_cio"]\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        '    result["ai_cio"] = transformation["ai_cio"]\n    result["process_optimizer"] = build_process_optimizer(result, artifacts_dir)\n    result["management_conclusion"] = build_management_conclusion(result, artifacts_dir)\n',
        'process optimizer result',
    )
    executive = executive.replace('2.0.0-alpha.14', '2.0.0-alpha.15')
    EXEC_PATH.write_text(executive, encoding='utf-8')

    dashboard = DASH_PATH.read_text(encoding='utf-8')
    dashboard = once(
        dashboard,
        '.cio-rank{display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;border-radius:50%;background:rgba(109,140,255,.18);margin-right:8px;font-weight:700}',
        '.cio-rank{display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;border-radius:50%;background:rgba(109,140,255,.18);margin-right:8px;font-weight:700}.process-score{font-size:28px;font-weight:800}.process-optimized{color:var(--ok)}.process-improvable{color:var(--warn)}.process-redesign{color:var(--bad)}.optimizer-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.optimizer-card{padding:14px;border-radius:12px;background:rgba(16,27,45,.8);border:1px solid var(--line)}.optimizer-rec{padding:13px 0;border-bottom:1px solid rgba(40,57,86,.65)}.optimizer-rec:last-child{border-bottom:0}@media(max-width:900px){.optimizer-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.optimizer-grid{grid-template-columns:1fr}}',
        'process optimizer styles',
    )
    dashboard = once(
        dashboard,
        'function render(d){\n',
        '''function processOptimizerHtml(d){
 const o=d.process_optimizer||{},s=o.summary||{},processes=o.processes||[],recs=o.top_recommendations||[];
 if(o.status!=='ok')return '<section class="section"><h2>AI Process Optimizer</h2><div class="empty">Недостаточно фактических данных для оценки качества процессов. Сначала необходимо накопить Process Mining и Deep REST Evidence.</div></section>';
 return '<section class="section"><h2>AI Process Optimizer</h2><div class="optimizer-grid"><div class="optimizer-card"><span class="status">Общая оценка</span><div class="process-score '+(Number(o.overall_score)>=80?'process-optimized':Number(o.overall_score)>=60?'process-improvable':'process-redesign')+'">'+esc(num(o.overall_score))+'</div><small>из 100</small></div><div class="optimizer-card"><span class="status">Процессов проверено</span><div class="process-score">'+esc(s.processes_analyzed||0)+'</div></div><div class="optimizer-card"><span class="status">Можно улучшить</span><div class="process-score process-improvable">'+esc(s.improvable||0)+'</div></div><div class="optimizer-card"><span class="status">Требует переработки</span><div class="process-score process-redesign">'+esc(s.redesign||0)+'</div></div></div>'+
 (processes.length?'<h3 style="margin-top:18px">Рейтинг процессов</h3>'+processes.slice(0,10).map(x=>'<div class="row"><span>'+esc(x.name)+'<br><small class="status">этапов '+esc((x.metrics||{}).stages||0)+' · запусков '+esc((x.metrics||{}).runs||0)+' · рекомендаций '+esc((x.recommendations||[]).length)+'</small></span><b class="process-'+esc(x.status||'improvable')+'">'+esc(num(x.score))+'</b></div>').join(''):'')+
 '<h3 style="margin-top:18px">Приоритетные рекомендации</h3>'+(recs.length?recs.map((x,i)=>'<div class="optimizer-rec"><h3>'+(i+1)+'. '+esc(x.process)+'</h3><p><b>Проблема:</b> '+esc(x.problem||'')+'</p><div class="decision"><b>Оптимизация</b><span>'+esc(x.recommendation||'')+'</span></div><p><b>Ожидаемый эффект:</b> '+esc(x.expected_effect||'')+'</p><span class="status">Категория: '+esc(x.category||'')+' · уверенность '+esc(x.confidence||0)+'%</span></div>').join(''):'<div class="empty">Подтверждённых рекомендаций не сформировано.</div>')+'<p class="status">'+esc(o.methodology||'')+'</p></section>';
}
function render(d){
''',
        'process optimizer renderer',
    )
    dashboard = once(
        dashboard,
        " let html=conclusionHtml(d)+executiveKpiHtml(d)+transformationHtml(d)+'<div class=\"summary\">",
        " let html=conclusionHtml(d)+executiveKpiHtml(d)+processOptimizerHtml(d)+transformationHtml(d)+'<div class=\"summary\">",
        'process optimizer placement',
    )
    dashboard = dashboard.replace('2.0.0-alpha.14', '2.0.0-alpha.15')
    DASH_PATH.write_text(dashboard, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH, REF_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.14', '2.0.0-alpha.15')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT AI Process Optimizer 2.0.0-alpha.15')


if __name__ == '__main__':
    main()
