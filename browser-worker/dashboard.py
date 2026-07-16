from __future__ import annotations


def dashboard_html() -> str:
    return r'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI-BIT Audit Dashboard</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2d;--line:#26324d;--text:#eef3ff;--muted:#9ba8c5;--ok:#38d996;--warn:#ffbd59;--bad:#ff637d;--accent:#6ea8fe}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--text)}
header{padding:24px 28px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:16px;align-items:center;position:sticky;top:0;background:rgba(11,16,32,.94);backdrop-filter:blur(12px);z-index:5}
h1{margin:0;font-size:24px}.muted{color:var(--muted)}button,select{background:#19233b;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:9px 12px}
main{padding:24px 28px;max-width:1600px;margin:auto}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}.metric{font-size:30px;font-weight:700;margin-top:8px}
section{margin-top:18px}.two{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}.bar{height:12px;background:#202b45;border-radius:8px;overflow:hidden}.bar>span{display:block;height:100%;background:var(--accent)}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:600}.pill{display:inline-block;padding:3px 8px;border-radius:999px;background:#24304a}.ok{color:var(--ok)}.partial,.redirected{color:var(--warn)}.denied,.error,.not_found{color:var(--bad)}
.tree{max-height:520px;overflow:auto}.node{padding:8px 10px;margin:4px 0;border-left:2px solid var(--line);background:#10182a;border-radius:6px}.node a{color:var(--text);text-decoration:none}.node a:hover{color:var(--accent)}
.diff li{margin:7px 0}.empty{padding:28px;text-align:center;color:var(--muted)}
@media(max-width:1000px){.grid{grid-template-columns:repeat(2,1fr)}.two{grid-template-columns:1fr}}@media(max-width:600px){header,main{padding:16px}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><div><h1>AI-BIT Audit Dashboard</h1><div class="muted">Карта портала, история и изменения</div></div><div><select id="audit"></select> <button id="refresh">Обновить</button></div></header>
<main>
<div class="grid">
 <div class="card"><div class="muted">Посещено</div><div class="metric" id="visited">—</div></div>
 <div class="card"><div class="muted">Обнаружено</div><div class="metric" id="scheduled">—</div></div>
 <div class="card"><div class="muted">Ошибки</div><div class="metric" id="errors">—</div></div>
 <div class="card"><div class="muted">Разделы</div><div class="metric" id="sections">—</div></div>
</div>
<section class="two">
 <div class="card"><h3>Покрытие по разделам</h3><div id="sectionBars"></div></div>
 <div class="card"><h3>Изменения с предыдущего аудита</h3><div id="diff" class="diff"></div></div>
</section>
<section class="two">
 <div class="card"><h3>Карта портала</h3><div id="tree" class="tree"></div></div>
 <div class="card"><h3>Страницы</h3><div style="overflow:auto;max-height:520px"><table><thead><tr><th>Раздел</th><th>Страница</th><th>Статус</th></tr></thead><tbody id="pages"></tbody></table></div></div>
</section>
</main>
<script>
const $=s=>document.querySelector(s);let history=[];
async function getJSON(url){const r=await fetch(url);if(!r.ok)throw new Error(await r.text());return r.json()}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function loadHistory(){history=await getJSON('/crawl/history');const sel=$('#audit');sel.innerHTML=history.map(x=>`<option value="${esc(x.id)}">${esc(x.created_at)} — ${x.summary?.visited??0} стр.</option>`).join('');if(history.length)await loadAudit(history[0].id);else showEmpty()}
function showEmpty(){$('#tree').innerHTML='<div class="empty">Запустите первый crawl</div>';$('#pages').innerHTML='';}
async function loadAudit(id){const data=await getJSON('/crawl/history/'+encodeURIComponent(id));const s=data.summary||{};$('#visited').textContent=s.visited??0;$('#scheduled').textContent=s.scheduled??0;$('#errors').textContent=s.errors??0;$('#sections').textContent=Object.keys(s.sections||{}).length;renderSections(s.sections||{});renderNodes(data.nodes||[]);await renderDiff(id)}
function renderSections(sections){const max=Math.max(1,...Object.values(sections));$('#sectionBars').innerHTML=Object.entries(sections).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<div style="margin:12px 0"><div style="display:flex;justify-content:space-between"><span>${esc(k)}</span><b>${v}</b></div><div class="bar"><span style="width:${Math.round(v/max*100)}%"></span></div></div>`).join('')}
function renderNodes(nodes){$('#pages').innerHTML=nodes.map(n=>`<tr><td>${esc(n.section)}</td><td><a href="${esc(n.url)}" target="_blank">${esc(n.title||n.url)}</a></td><td><span class="pill ${esc(n.status)}">${esc(n.status)}</span></td></tr>`).join('');$('#tree').innerHTML=nodes.sort((a,b)=>(a.depth??0)-(b.depth??0)).map(n=>`<div class="node" style="margin-left:${Math.min(6,n.depth||0)*18}px"><span class="muted">${esc(n.section)}</span> · <a href="${esc(n.url)}" target="_blank">${esc(n.title||n.url)}</a></div>`).join('')}
async function renderDiff(id){const idx=history.findIndex(x=>x.id===id);if(idx<0||idx===history.length-1){$('#diff').innerHTML='<div class="empty">Нет предыдущего аудита для сравнения</div>';return}const before=history[idx+1].id;const d=await getJSON(`/crawl/diff?before=${encodeURIComponent(before)}&after=${encodeURIComponent(id)}`);$('#diff').innerHTML=`<div class="grid" style="grid-template-columns:repeat(3,1fr)"><div><b class="ok">+${d.summary.added}</b><div class="muted">добавлено</div></div><div><b class="denied">-${d.summary.removed}</b><div class="muted">удалено</div></div><div><b>${d.summary.changed}</b><div class="muted">изменено</div></div></div><ul>${d.added.slice(0,8).map(x=>`<li class="ok">+ ${esc(x.title||x.url)}</li>`).join('')}${d.removed.slice(0,8).map(x=>`<li class="denied">− ${esc(x.title||x.url)}</li>`).join('')}</ul>`}
$('#audit').addEventListener('change',e=>loadAudit(e.target.value));$('#refresh').addEventListener('click',loadHistory);loadHistory().catch(e=>{$('#tree').innerHTML='<div class="empty">'+esc(e.message)+'</div>'});
</script>
</body></html>'''
