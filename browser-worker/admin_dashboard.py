from __future__ import annotations


def admin_dashboard_html() -> str:
    return r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI-BIT Enterprise Admin</title><style>
:root{color-scheme:dark;--bg:#07101d;--panel:#101b2d;--line:#283956;--text:#eef5ff;--muted:#91a3bd;--accent:#62a0ff}*{box-sizing:border-box}body{margin:0;font:14px/1.5 Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--text);overflow:hidden}header{height:72px;padding:14px 22px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;background:#07101df5}.brand h1{margin:0;font-size:20px}.brand div{color:var(--muted);font-size:12px}.tabs{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.tab{background:#172640;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:9px 12px;cursor:pointer}.tab.active{border-color:var(--accent);background:#20365a}.status{color:var(--muted);font-size:12px;margin-left:10px}.framewrap{height:calc(100vh - 72px);position:relative}.frame{position:absolute;inset:0;width:100%;height:100%;border:0;display:none;background:var(--bg)}.frame.active{display:block}@media(max-width:1250px){header{height:auto;align-items:flex-start;gap:10px;flex-direction:column}.framewrap{height:calc(100vh - 132px)}.status{margin-left:0}}
</style></head><body><header><div class="brand"><h1>AI-BIT Enterprise Admin</h1><div>1.0.0-rc.3 · единая консоль аудита, аналитики, AI и диагностики</div></div><div><div class="tabs" id="tabs"><button class="tab active" data-key="executive">Executive</button><button class="tab" data-key="implementation">Внедрение</button><button class="tab" data-key="operations">Операции</button><button class="tab" data-key="processes">Process Mining</button><button class="tab" data-key="architecture">Бизнес-архитектура</button><button class="tab" data-key="system">Система</button></div><div class="status" id="status">Раздел: Executive</div></div></header><main class="framewrap" id="frames">
<iframe class="frame active" data-key="executive" data-src="/executive"></iframe>
<iframe class="frame" data-key="implementation" data-src="/dashboard"></iframe>
<iframe class="frame" data-key="operations" data-src="/operations"></iframe>
<iframe class="frame" data-key="processes" data-src="/processes"></iframe>
<iframe class="frame" data-key="architecture" data-src="/business-architecture"></iframe>
<iframe class="frame" data-key="system" data-src="/system"></iframe>
</main><script>
const names={executive:'Executive',implementation:'Аудит внедрения',operations:'Operational Intelligence',processes:'Process Mining',architecture:'Business Architecture',system:'System Health'};
function activate(key){document.querySelectorAll('.tab,.frame').forEach(x=>x.classList.remove('active'));const tab=document.querySelector(`.tab[data-key="${key}"]`);const frame=document.querySelector(`.frame[data-key="${key}"]`);if(!tab||!frame)return;tab.classList.add('active');frame.classList.add('active');if(!frame.src)frame.src=frame.dataset.src;history.replaceState(null,'','#'+key);document.querySelector('#status').textContent='Раздел: '+names[key]}
document.querySelector('#tabs').addEventListener('click',e=>{if(e.target.dataset.key)activate(e.target.dataset.key)});activate(location.hash.slice(1)||'executive');window.addEventListener('hashchange',()=>activate(location.hash.slice(1)||'executive'));
</script></body></html>'''
