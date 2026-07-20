from __future__ import annotations

from pathlib import Path

APP_PATH = Path('/app/app.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')
REF_PATH = Path('/app/reference_model.py')
EXEC_PATH = Path('/app/executive_intelligence.py')
PROCESS_OPTIMIZER_PATH = Path('/app/process_optimizer.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    app = APP_PATH.read_text(encoding='utf-8')
    if 'from release_manifest import get_release_manifest' not in app:
        app += '''\n\nfrom release_manifest import get_release_manifest\n\n\n@app.get("/about")\ndef about_release() -> dict:\n    return get_release_manifest()\n'''
    app = app.replace('2.0.0-alpha.15', '2.1.0')
    APP_PATH.write_text(app, encoding='utf-8')

    dashboard = DASH_PATH.read_text(encoding='utf-8')
    dashboard = once(
        dashboard,
        '.optimizer-rec:last-child{border-bottom:0}',
        '.optimizer-rec:last-child{border-bottom:0}.about-release{padding:18px;border-radius:14px;background:linear-gradient(135deg,rgba(109,140,255,.14),rgba(57,208,193,.08));border:1px solid rgba(109,140,255,.3)}.about-release h2{margin-bottom:5px}.about-release-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}.about-release-item{padding:12px;border-radius:10px;background:rgba(16,27,45,.72);border:1px solid var(--line)}@media(max-width:760px){.about-release-grid{grid-template-columns:1fr}}',
        'release about styles',
    )
    dashboard = once(
        dashboard,
        'function render(d){\n',
        '''function releaseAboutHtml(){
 return '<section class="section about-release"><h2>AI-BIT Enterprise 2.1.0</h2><p>Intelligent Transformation Suite — доказательный аудит, оптимизация процессов и управленческие рекомендации для Bitrix24.</p><div class="about-release-grid"><div class="about-release-item"><b>Доказательная модель</b><br><small>Неизвестное не считается отсутствующим.</small></div><div class="about-release-item"><b>Управленческий контур</b><br><small>KPI, причины, экономика, roadmap и AI CIO.</small></div><div class="about-release-item"><b>Разработчик</b><br><small>Коваленко А.С. · pizzakov@gmail.com</small></div></div></section>';
}
function render(d){
''',
        'release about renderer',
    )
    dashboard = once(
        dashboard,
        " let html=conclusionHtml(d)+executiveKpiHtml(d)+processOptimizerHtml(d)+transformationHtml(d)+'<div class=\"summary\">",
        " let html=releaseAboutHtml()+conclusionHtml(d)+executiveKpiHtml(d)+processOptimizerHtml(d)+transformationHtml(d)+'<div class=\"summary\">",
        'release about placement',
    )
    dashboard = dashboard.replace('2.0.0-alpha.15', '2.1.0')
    DASH_PATH.write_text(dashboard, encoding='utf-8')

    for path in (ADMIN_PATH, REF_PATH, EXEC_PATH, PROCESS_OPTIMIZER_PATH):
        text = path.read_text(encoding='utf-8').replace('2.0.0-alpha.15', '2.1.0')
        path.write_text(text, encoding='utf-8')

    print('Applied AI-BIT Enterprise 2.1.0 — Intelligent Transformation Suite')


if __name__ == '__main__':
    main()
