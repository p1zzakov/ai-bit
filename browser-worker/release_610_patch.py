from __future__ import annotations

import re
from pathlib import Path

MODULE = Path('/app/project_intelligence.py')
ADMIN = Path('/app/admin_dashboard.py')
MANIFEST = Path('/app/release_manifest.py')
VERSION = '6.1.0'

NEW_HTML = r'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Project Analyst</title>
<style>
:root{color-scheme:light;--bg:#f5f6f8;--surface:#fff;--surface2:#fafbfc;--line:#e1e5ea;--text:#17191c;--muted:#70757d;--accent:#5e6ad2;--ok:#16835d;--warn:#a9670b;--bad:#b42318}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 Inter,Segoe UI,sans-serif}main{max-width:1500px;margin:auto;padding:24px}.grid{display:grid;grid-template-columns:340px minmax(0,1fr);gap:12px}.panel{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:10px}.head{padding:13px 15px;border-bottom:1px solid var(--line);background:var(--surface2);font-weight:800}.body{padding:14px}.item{padding:11px;border:1px solid var(--line);border-radius:9px;margin:7px 0;cursor:pointer}.item:hover,.item.active{border-color:var(--accent);background:#f7f7ff}.muted{color:var(--muted)}input,select,textarea{width:100%;padding:9px 10px;margin:5px 0 10px;border:1px solid var(--line);border-radius:8px;font:inherit;background:#fff}textarea{min-height:78px;resize:vertical}.btn{padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer}.btn:hover{background:#f4f5f7}.btn.primary{background:#202124;border-color:#202124;color:#fff}.btn.accent{background:var(--accent);border-color:var(--accent);color:#fff}.btn:disabled{opacity:.55;cursor:wait}.actions{display:flex;gap:8px;flex-wrap:wrap}.tabs{display:flex;gap:2px;border-bottom:1px solid var(--line);overflow:auto}.tab{padding:11px 13px;border:0;background:none;cursor:pointer;white-space:nowrap}.tab.active{border-bottom:2px solid var(--accent);font-weight:800;color:var(--accent)}.view{display:none;padding:14px}.view.active{display:block}.badge{display:inline-flex;padding:3px 8px;border-radius:999px;background:#eef0f2;font-size:10px;font-weight:800;text-transform:uppercase}.error{padding:11px;border:1px solid #f2b8b5;background:#fff1f0;color:var(--bad);border-radius:8px;margin-bottom:10px}.success{padding:11px;border:1px solid #a7dfc5;background:#edf9f3;color:var(--ok);border-radius:8px;margin-bottom:10px}pre{white-space:pre-wrap;overflow:auto;background:#f8f9fa;padding:12px;border-radius:8px;border:1px solid var(--line)}h1{margin:5px 0 4px}.eyebrow{font-size:11px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--accent)}@media(max-width:900px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<main id="app">
<div class="eyebrow">AI-BIT Enterprise 6.1</div><h1>AI Project Analyst</h1>
<p class="muted">Word/PDF/Excel → требования → конфликты → интервью → MCP → документы</p>
<div id="notice"></div>
<div class="grid">
<aside>
<div class="panel"><div class="head">Новый проект</div><div class="body">
<form data-form="create-project">
<input name="title" placeholder="Название проекта" required>
<select name="project_type"><option value="onec_report">Отчёт 1С</option><option value="onec_print_form">Печатная форма 1С</option><option value="onec_change">Доработка 1С</option><option value="integration">Интеграция</option><option value="dashboard">Dashboard</option><option value="business_process">Бизнес-процесс</option><option value="rest_api">REST API</option><option value="custom">Другой проект</option></select>
<textarea name="description" placeholder="Кратко опишите задачу"></textarea>
<input type="file" name="files" multiple accept=".docx,.pdf,.xlsx,.xlsm,.txt,.md,.csv">
<button class="btn primary" type="submit">Создать проект</button>
</form></div></div>
<div class="panel"><div class="head">Проекты</div><div class="body" id="projectList"><span class="muted">Загрузка…</span></div></div>
</aside>
<section class="panel">
<div class="head" id="projectTitle">Выберите проект</div>
<div class="tabs" id="tabs">
<button class="tab active" data-tab="overview">Обзор</button><button class="tab" data-tab="materials">Материалы</button><button class="tab" data-tab="requirements">Требования</button><button class="tab" data-tab="interview">Интервью</button><button class="tab" data-tab="review">AI Review</button><button class="tab" data-tab="documents">Документы</button>
</div>
<div class="view active" data-view="overview"></div><div class="view" data-view="materials"></div><div class="view" data-view="requirements"></div><div class="view" data-view="interview"></div><div class="view" data-view="review"></div><div class="view" data-view="documents"></div>
</section>
</div>
</main>
<script>
(()=>{
'use strict';
const state={projects:[],project:null,tab:'overview',busy:false};
const root=document.getElementById('app');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(url,options={}){const response=await fetch(url,options);const text=await response.text();let payload=null;try{payload=text?JSON.parse(text):null}catch{payload=text}if(!response.ok)throw new Error(typeof payload==='string'?payload:(payload?.detail||JSON.stringify(payload)));return payload}
function notice(message,type='error'){document.getElementById('notice').innerHTML=message?`<div class="${type}">${esc(message)}</div>`:''}
function setBusy(value){state.busy=value;root.querySelectorAll('button').forEach(button=>button.disabled=value)}
async function run(task,success=''){if(state.busy)return;setBusy(true);notice('');try{await task();if(success)notice(success,'success')}catch(error){console.error(error);notice(error.message||String(error))}finally{setBusy(false)}}
async function loadProjects(){const data=await api('/project-intelligence/api/projects');state.projects=data.projects||[];renderProjects()}
async function openProject(id){state.project=await api('/project-intelligence/api/projects/'+encodeURIComponent(id));renderAll()}
function renderProjects(){const box=document.getElementById('projectList');box.innerHTML=state.projects.length?state.projects.map(p=>`<div class="item ${state.project?.id===p.id?'active':''}" data-action="open-project" data-id="${esc(p.id)}"><b>${esc(p.title)}</b><div class="muted">${esc(p.status)} · r${esc(p.revision)}</div></div>`).join(''):'<span class="muted">Проектов пока нет</span>'}
function activateTab(name){state.tab=name;root.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x.dataset.tab===name));root.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x.dataset.view===name))}
function renderAll(){renderProjects();const p=state.project;document.getElementById('projectTitle').textContent=p?p.title:'Выберите проект';const empty='<span class="muted">Сначала выберите или создайте проект</span>';if(!p){root.querySelectorAll('[data-view]').forEach(v=>v.innerHTML=empty);return}
const analysis=p.analysis||null;const approval=p.approval||null;
view('overview',`<p>Статус: <span class="badge">${esc(p.status)}</span></p><p>Материалов: <b>${p.materials?.length||0}</b> · требований: <b>${p.requirements?.length||0}</b> · конфликтов: <b>${p.conflicts?.length||0}</b></p><div class="actions"><button class="btn primary" data-action="analyze">Запустить AI Review</button><button class="btn" data-action="approve">Утвердить и сформировать документы</button></div>${approval?`<p class="muted">Последнее решение: ${approval.approved?'утверждено':'отклонено'}</p>`:''}`);
view('materials',`<form data-form="add-materials"><input type="file" name="files" multiple accept=".docx,.pdf,.xlsx,.xlsm,.txt,.md,.csv"><button class="btn" type="submit">Добавить материалы</button></form>${(p.materials||[]).map(m=>`<div class="item"><b>${esc(m.filename)}</b><div class="muted">${esc(m.analysis?.format||'unknown')} · ${Math.round((m.size||0)/1024)} КБ</div></div>`).join('')||'<span class="muted">Нет материалов</span>'}`);
view('requirements',(p.requirements||[]).map(r=>`<div class="item"><b>${esc(r.id)}</b><div>${esc(r.text)}</div><div class="muted">Источник: ${esc(r.source_file||'не определён')}</div></div>`).join('')||'<span class="muted">Требования не извлечены</span>');
view('interview',`<form data-form="answers">${(p.questions||[]).map(q=>`<label><b>${esc(q.question)}</b>${q.required?' *':''}</label><textarea name="${esc(q.id)}">${esc(p.answers?.[q.id]||'')}</textarea>`).join('')}<button class="btn primary" type="submit">Сохранить ответы</button></form>`);
view('review',analysis?`<h3>Готовность: ${esc(analysis.readiness)}%</h3><p>Статус: <span class="badge">${esc(analysis.status)}</span></p><pre>${esc(JSON.stringify(analysis,null,2))}</pre>`:'<span class="muted">Нажмите «Запустить AI Review»</span>');
view('documents',p.documents?Object.entries(p.documents).map(([key,d])=>`<div class="item"><a target="_blank" rel="noopener" href="/project-intelligence/api/projects/${encodeURIComponent(p.id)}/documents/${encodeURIComponent(key)}.md"><b>${esc(d.document||key)}</b></a></div>`).join(''):'<span class="muted">Документы появятся после утверждения</span>');activateTab(state.tab)}
function view(name,html){const node=root.querySelector(`[data-view="${name}"]`);if(node)node.innerHTML=html}
root.addEventListener('click',event=>{const target=event.target.closest('[data-action],[data-tab]');if(!target)return;if(target.dataset.tab){activateTab(target.dataset.tab);return}const action=target.dataset.action;if(action==='open-project')run(()=>openProject(target.dataset.id));if(!state.project)return;if(action==='analyze')run(async()=>{await api(`/project-intelligence/api/projects/${state.project.id}/analyze`,{method:'POST'});await openProject(state.project.id)},'AI Review выполнен');if(action==='approve')run(async()=>{await api(`/project-intelligence/api/projects/${state.project.id}/approve`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approved:true,comment:''})});await openProject(state.project.id);activateTab('documents')},'Документы сформированы')});
root.addEventListener('submit',event=>{event.preventDefault();const form=event.target;const kind=form.dataset.form;if(kind==='create-project')run(async()=>{state.project=await api('/project-intelligence/api/projects',{method:'POST',body:new FormData(form)});form.reset();await loadProjects();renderAll()},'Проект создан');if(!state.project)return;if(kind==='add-materials')run(async()=>{await api(`/project-intelligence/api/projects/${state.project.id}/materials`,{method:'POST',body:new FormData(form)});await openProject(state.project.id)},'Материалы добавлены');if(kind==='answers')run(async()=>{const answers={};new FormData(form).forEach((value,key)=>answers[key]=value);await api(`/project-intelligence/api/projects/${state.project.id}/answers`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answers})});await openProject(state.project.id)},'Ответы сохранены')});
run(async()=>{await loadProjects();if(state.projects[0])await openProject(state.projects[0].id)});
})();
</script>
</body></html>'''


def patch_module(text: str) -> str:
    pattern = r"HTML\s*=\s*'''[\s\S]*?'''\s*$"
    replacement = "HTML = r'''" + NEW_HTML.replace("'''", "\\'\\'\\'") + "'''\n"
    patched, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise RuntimeError('6.1.0 cannot locate Project Intelligence HTML block')
    patched = patched.replace("VERSION='6.0.0'", "VERSION='6.1.0'")
    patched = patched.replace('VERSION="6.0.0"', 'VERSION="6.1.0"')
    return patched


def clean_admin(text: str) -> str:
    # Remove malformed navigation leftovers produced by older fallback patches.
    text = re.sub(r'<button\b[^>]*>[\s\S]*?undefined[\s\S]*?</button>', '', text, flags=re.I)
    text = re.sub(r'(?:undefined\s*){2,}', '', text)
    for old in ('6.0.0', '5.1.0'):
        text = text.replace(old, VERSION)
    return text


def main() -> None:
    if not MODULE.exists():
        raise RuntimeError('6.1.0 project_intelligence.py not generated')
    module = patch_module(MODULE.read_text(encoding='utf-8'))
    compile(module, str(MODULE), 'exec')
    MODULE.write_text(module, encoding='utf-8')
    print('[OK] Project Intelligence state-driven frontend compiled')

    if ADMIN.exists():
        admin = clean_admin(ADMIN.read_text(encoding='utf-8'))
        ADMIN.write_text(admin, encoding='utf-8')
        if 'data-key="projectIntelligence"' not in admin:
            raise RuntimeError('6.1.0 Project Intelligence navigation missing')
        print('[OK] Unified Admin navigation cleaned')

    if MANIFEST.exists():
        manifest = MANIFEST.read_text(encoding='utf-8')
        manifest = manifest.replace('6.0.0', VERSION).replace('5.1.0', VERSION)
        MANIFEST.write_text(manifest, encoding='utf-8')

    print('Applied AI-BIT Enterprise 6.1.0 — Project Intelligence Frontend Stabilization')


if __name__ == '__main__':
    main()
