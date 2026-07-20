from __future__ import annotations

from pathlib import Path

ADMIN = Path('/app/admin_dashboard.py')
APP = Path('/app/app.py')
MANIFEST = Path('/app/release_manifest.py')

ADMIN_SOURCE = r'''from __future__ import annotations


def admin_dashboard_html() -> str:
    return r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI-BIT Enterprise</title>
<style>
:root{color-scheme:light;--bg:#f6f7f9;--surface:#fff;--surface2:#f9fafb;--line:#e5e7eb;--line2:#d8dce3;--text:#17191c;--muted:#747982;--accent:#5e6ad2;--accent-soft:#eef0ff;--ok:#14865f;--warn:#b7791f;--bad:#cf3c4f;--shadow:0 1px 2px rgba(15,23,42,.04),0 10px 30px rgba(15,23,42,.05)}
*{box-sizing:border-box}html,body{height:100%}body{margin:0;overflow:hidden;background:var(--bg);color:var(--text);font:14px/1.45 Inter,Segoe UI,Arial,sans-serif}button{font:inherit}.shell{height:100%;display:grid;grid-template-columns:196px minmax(0,1fr)}
.sidebar{display:flex;min-height:0;flex-direction:column;border-right:1px solid var(--line);background:#fbfbfc;padding:14px 10px 12px}.brand{display:flex;align-items:center;gap:9px;padding:2px 9px 18px}.logo{width:32px;height:32px;border-radius:9px;display:grid;place-items:center;background:linear-gradient(135deg,#6875e8,#8b5cf6);color:#fff;font-weight:800;box-shadow:0 6px 18px rgba(94,106,210,.2)}.brand h1{font-size:13px;margin:0}.brand p{font-size:9px;color:var(--muted);margin:1px 0 0}.section-label{padding:4px 10px 7px;color:#9aa0aa;font-size:8px;font-weight:800;letter-spacing:.9px;text-transform:uppercase}.nav{display:flex;flex-direction:column;gap:2px;min-height:0;overflow:auto}.nav button{width:100%;display:flex;align-items:center;gap:9px;border:0;background:transparent;color:#5d626b;padding:7px 8px;border-radius:7px;text-align:left;cursor:pointer;transition:.15s}.nav button:hover{background:#f0f1f3;color:#202226}.nav button.active{background:#ececef;color:#17191c;font-weight:600}.icon{width:21px;height:21px;border-radius:6px;display:grid;place-items:center;background:#eef0f2;color:#777d86;font-size:9px;font-weight:800}.nav button.active .icon{background:var(--accent-soft);color:var(--accent)}
.sidebar-bottom{margin-top:auto;padding:12px 7px 0}.health{padding:10px;border:1px solid var(--line);border-radius:9px;background:var(--surface)}.health-row{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:11px}.dot{width:7px;height:7px;border-radius:50%;background:#a8adb5}.dot.ok{background:#22a06b}.dot.warning{background:#e5a439}.dot.error{background:#df5466}.health small{display:block;color:var(--muted);font-size:9px;margin-top:5px}.version{margin-top:8px;text-align:center;color:#a0a5ad;font-size:9px}
.workspace{min-width:0;display:grid;grid-template-rows:58px minmax(0,1fr)}.topbar{display:flex;align-items:center;justify-content:space-between;padding:0 16px;border-bottom:1px solid var(--line);background:rgba(255,255,255,.94);backdrop-filter:blur(14px)}.page-title h2{font-size:13px;margin:0}.page-title p{font-size:9px;color:var(--muted);margin:2px 0 0}.actions{display:flex;gap:7px}.action{border:1px solid var(--line2);background:#fff;color:#575c65;padding:7px 10px;border-radius:7px;cursor:pointer}.action:hover{background:#f7f7f8}.action.primary{background:#202124;border-color:#202124;color:#fff}.content{min-height:0;padding:12px}.viewport{height:100%;position:relative;overflow:hidden;border:1px solid var(--line);border-radius:10px;background:var(--surface);box-shadow:var(--shadow)}.frame{position:absolute;inset:0;width:100%;height:100%;border:0;display:none;background:#fff}.frame.active{display:block}.loader{position:absolute;inset:0;z-index:5;display:none;place-items:center;background:rgba(255,255,255,.72);backdrop-filter:blur(2px)}.loader.show{display:grid}.spinner{width:28px;height:28px;border:3px solid #e5e7eb;border-top-color:var(--accent);border-radius:50%;animation:spin .75s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.error-panel{display:none;position:absolute;inset:20px;z-index:6;place-items:center;text-align:center}.error-panel.show{display:grid}.error-card{max-width:480px;border:1px solid #f1c5cb;background:#fff7f8;border-radius:12px;padding:22px}.error-card h3{margin:0 0 7px;color:#9f2435}.error-card p{margin:0 0 14px;color:#6b3a42}.error-card button{border:0;border-radius:7px;padding:8px 12px;background:#9f2435;color:#fff;cursor:pointer}
.dev{position:fixed;right:16px;bottom:14px;z-index:20}.dev button{width:25px;height:25px;border-radius:50%;border:1px solid var(--line2);background:#fff;color:#69707a;cursor:help}.dev span{position:absolute;right:0;bottom:33px;display:none;white-space:nowrap;border:1px solid var(--line);border-radius:8px;background:#fff;padding:8px 10px;box-shadow:var(--shadow);color:#5d626b;font-size:11px}.dev:hover span,.dev:focus-within span{display:block}
@media(max-width:920px){.shell{grid-template-columns:70px minmax(0,1fr)}.brand{justify-content:center;padding-inline:0}.brand>div:not(.logo),.section-label,.nav .label,.sidebar-bottom{display:none}.nav button{justify-content:center}.icon{width:32px;height:32px}.content{padding:8px}}
</style>
</head>
<body>
<div class="shell">
<aside class="sidebar">
 <div class="brand"><div class="logo">AI</div><div><h1>AI-BIT Enterprise</h1><p>Business Intelligence Platform</p></div></div>
 <div class="section-label">Рабочее пространство</div>
 <nav class="nav" id="nav"></nav>
 <div class="sidebar-bottom"><div class="health"><div class="health-row"><span>Состояние системы</span><span class="dot" id="healthDot"></span></div><small id="healthText">Проверяю источники…</small></div><div class="version">AI-BIT · 3.4.2</div></div>
</aside>
<section class="workspace">
 <header class="topbar"><div class="page-title"><h2 id="title">AI-BIT Enterprise</h2><p id="subtitle">Загрузка раздела…</p></div><div class="actions"><button class="action" id="openDirect" type="button">Открыть отдельно</button><button class="action primary" id="refresh" type="button">Обновить раздел</button></div></header>
 <main class="content"><div class="viewport" id="viewport"><div class="loader" id="loader"><div class="spinner"></div></div><div class="error-panel" id="errorPanel"><div class="error-card"><h3>Не удалось открыть раздел</h3><p id="errorText">Раздел временно недоступен.</p><button id="retry" type="button">Повторить</button></div></div></div></main>
</section>
</div>
<div class="dev"><button type="button" aria-label="Информация о разработчике">i</button><span><b>Разработчик: Коваленко А.С.</b><br>pizzakov@gmail.com</span></div>
<script>
(()=>{'use strict';
const sections={
 executive:{icon:'E',label:'Executive',title:'Executive Dashboard',subtitle:'Ключевые показатели, риски и рекомендации',url:'/executive'},
 implementation:{icon:'I',label:'Аудит внедрения',title:'Аудит внедрения',subtitle:'Зрелость модулей, страницы и план развития',url:'/dashboard'},
 operations:{icon:'O',label:'Операции',title:'Operational Intelligence',subtitle:'Нагрузка, просрочка и аналитика подразделений',url:'/operations'},
 processes:{icon:'P',label:'Process Mining',title:'Process Mining',subtitle:'Повторяющиеся операции и кандидаты на автоматизацию',url:'/processes'},
 architecture:{icon:'B',label:'Бизнес-архитектура',title:'Бизнес-архитектура',subtitle:'Процессы, CRM-воронки и документооборот',url:'/business-architecture'},
 reports:{icon:'R',label:'Отчёты',title:'Reports & Export',subtitle:'Управленческие отчёты HTML, JSON и PDF',url:'/reports-ui'},
 management:{icon:'M',label:'Отчёт для руководства',title:'Отчёт для руководства',subtitle:'Понятная управленческая сводка без технического жаргона',url:'/management-report?embedded=1'},
 intelligence:{icon:'X',label:'Executive Intelligence',title:'Executive Intelligence Suite',subtitle:'Цифровая зрелость, риски, ROI и дорожная карта',url:'/executive-intelligence?embedded=1'},
 integrator:{icon:'T',label:'Интегратору',title:'Для интегратора',subtitle:'Технические отклонения, доказательства и план исправлений',url:'/integrator?embedded=1'},
 automation:{icon:'A',label:'Автоматизация',title:'Scheduling & Automation',subtitle:'Расписания, ручные запуски и журнал выполнения',url:'/automation'},
 system:{icon:'S',label:'Система',title:'Система и качество данных',subtitle:'Источники, права, свежесть и диагностика',url:'/system'},
 about:{icon:'?',label:'О системе',title:'О системе',subtitle:'Версия, принципы и информация о продукте',url:'/about'}
};
const dom=(selector,root=document)=>root.querySelector(selector);
const all=(selector,root=document)=>Array.from(root.querySelectorAll(selector));
const nav=dom('#nav'),viewport=dom('#viewport'),loader=dom('#loader'),errorPanel=dom('#errorPanel'),errorText=dom('#errorText');
let current='executive';
function setLoading(value){loader?.classList.toggle('show',Boolean(value));}
function setError(message=''){if(errorText)errorText.textContent=message||'Раздел временно недоступен.';errorPanel?.classList.toggle('show',Boolean(message));}
function build(){if(!nav||!viewport)return false;Object.entries(sections).forEach(([key,item])=>{const button=document.createElement('button');button.type='button';button.dataset.key=key;button.innerHTML=`<span class="icon">${item.icon}</span><span class="label">${item.label}</span>`;nav.appendChild(button);const frame=document.createElement('iframe');frame.className='frame';frame.dataset.key=key;frame.dataset.src=item.url;frame.title=item.title;viewport.appendChild(frame)});return true}
function normalize(key){return Object.prototype.hasOwnProperty.call(sections,key)?key:'executive'}
function frameFor(key){return dom(`.frame[data-key="${CSS.escape(key)}"]`)}
function buttonFor(key){return dom(`.nav button[data-key="${CSS.escape(key)}"]`)}
function loadFrame(frame,key,force=false){if(!frame)return;setError('');setLoading(true);const done=()=>setLoading(false);frame.addEventListener('load',done,{once:true});frame.addEventListener('error',()=>{setLoading(false);setError(`Не удалось загрузить раздел «${sections[key].title}».`)},{once:true});if(force||!frame.getAttribute('src')){const separator=sections[key].url.includes('?')?'&':'?';frame.src=sections[key].url+(force?separator+'_='+Date.now():'')}}
function navigate(rawKey,{replaceHash=true,force=false}={}){const key=normalize(rawKey);const button=buttonFor(key),frame=frameFor(key);if(!button||!frame){console.error('AI-BIT navigation registry mismatch',{key,button:Boolean(button),frame:Boolean(frame)});setError('Конфигурация раздела повреждена. Обновите страницу после пересборки контейнера.');return}current=key;all('.nav button.active,.frame.active').forEach(el=>el.classList.remove('active'));button.classList.add('active');frame.classList.add('active');const item=sections[key];const title=dom('#title'),subtitle=dom('#subtitle');if(title)title.textContent=item.title;if(subtitle)subtitle.textContent=item.subtitle;loadFrame(frame,key,force);if(replaceHash&&location.hash!==`#${key}`)history.replaceState(null,'',`#${key}`)}
if(build()){
 nav.addEventListener('click',event=>{const button=event.target.closest('button[data-key]');if(button)navigate(button.dataset.key)});
 dom('#refresh')?.addEventListener('click',()=>navigate(current,{force:true}));
 dom('#openDirect')?.addEventListener('click',()=>window.open(sections[current].url.replace(/[?&]embedded=1/,'').replace('?&','?').replace(/\?$/,''),'_blank','noopener'));
 dom('#retry')?.addEventListener('click',()=>navigate(current,{force:true}));
 window.addEventListener('hashchange',()=>navigate(location.hash.slice(1),{replaceHash:false}));
 navigate(location.hash.slice(1),{replaceHash:false});
}else{setError('Не удалось инициализировать рабочее пространство.')}
async function health(){const dot=dom('#healthDot'),text=dom('#healthText');try{const response=await fetch('/system/health?_='+Date.now(),{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);const data=await response.json();const status=data.overall_status||'warning';if(dot)dot.className='dot '+(status==='ok'?'ok':status==='error'?'error':'warning');if(text)text.textContent=status==='ok'?'Все ключевые источники доступны':status==='error'?'Есть критические ошибки':'Есть предупреждения по данным'}catch(error){if(dot)dot.className='dot error';if(text)text.textContent='Диагностика недоступна'}}
health();setInterval(health,60000);
})();
</script>
</body></html>"""
'''


def main() -> None:
    ADMIN.write_text(ADMIN_SOURCE, encoding='utf-8')

    if APP.exists():
        text = APP.read_text(encoding='utf-8')
        text = text.replace('"version": "3.4.0"', '"version": "3.4.2"')
        text = text.replace('"version": "3.4.1"', '"version": "3.4.2"')
        APP.write_text(text, encoding='utf-8')

    if MANIFEST.exists():
        text = MANIFEST.read_text(encoding='utf-8')
        for old in ('VERSION = "3.4.0"', 'VERSION = "3.4.1"'):
            text = text.replace(old, 'VERSION = "3.4.2"')
        MANIFEST.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Enterprise 3.4.2 — Frontend Stabilization')


if __name__ == '__main__':
    main()
