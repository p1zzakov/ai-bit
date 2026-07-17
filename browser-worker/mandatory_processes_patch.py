from __future__ import annotations

from pathlib import Path

EXEC_PATH = Path('/app/executive_intelligence.py')
DASH_PATH = Path('/app/management_report_dashboard.py')
APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    text = EXEC_PATH.read_text(encoding='utf-8')
    text = once(
        text,
        '    pm_summary = process_mining.get("summary") or operations.get("process_mining_summary") or {}\n',
        '''    pm_summary = process_mining.get("summary") or operations.get("process_mining_summary") or {}\n\n    # Mandatory target capabilities confirmed by the process owner. These are\n    # explicit business requirements, not heuristic findings from the crawler.\n    missing_capabilities = [\n        {\n            "id": "electronic_document_exchange",\n            "title": "Электронный обмен документами",\n            "status": "not_implemented",\n            "area": "Документооборот",\n            "impact": "Документы передаются и контролируются вне единого цифрового контура; отсутствует прозрачная история движения и исполнения.",\n            "decision": "Утвердить целевую схему электронного обмена документами, перечень типов документов и ответственных владельцев.",\n            "priority": 100,\n        },\n        {\n            "id": "contract_approval",\n            "title": "Согласование договоров",\n            "status": "not_implemented",\n            "area": "Документооборот",\n            "impact": "Нет единого маршрута, сроков согласования, контроля замечаний и итоговой версии договора.",\n            "decision": "Утвердить маршрут согласования договоров, роли, сроки, замещение и правила эскалации.",\n            "priority": 98,\n        },\n        {\n            "id": "user_provisioning_request",\n            "title": "Заявка на создание пользователя в AD и 1С",\n            "status": "not_implemented",\n            "area": "Внутренние заявки",\n            "impact": "Создание доступов выполняется вручную и без единой подтверждаемой цепочки согласования, сроков и контроля полноты выдаваемых прав.",\n            "decision": "Утвердить единую заявку на приём сотрудника с согласованием руководителя, кадровой службы, ИТ и владельца 1С.",\n            "priority": 95,\n        },\n        {\n            "id": "internal_memos",\n            "title": "Служебные записки",\n            "status": "not_implemented",\n            "area": "Внутренний документооборот",\n            "impact": "Служебные обращения не имеют единого реестра, маршрута, сроков исполнения и прозрачного статуса.",\n            "decision": "Утвердить типовые формы служебных записок и единый маршрут регистрации, согласования и исполнения.",\n            "priority": 90,\n        },\n    ]\n''',
        'mandatory capability registry',
    )
    text = once(
        text,
        '    automation = _clamp(_num(pm_summary.get("automation_score"), 0) or min(85, 35 + _num(pm_summary.get("automation_candidates")) * 2.5))\n    operations_score = _clamp(task_discipline * 0.7 + management * 0.3)\n',
        '''    automation = _clamp(_num(pm_summary.get("automation_score"), 0) or min(85, 35 + _num(pm_summary.get("automation_candidates")) * 2.5))\n    # Explicitly missing core processes must affect maturity. Penalties are\n    # deterministic and visible in the executive result.\n    bp_score = _clamp(bp_score - 12)\n    document_score = _clamp(document_score - 25)\n    automation = _clamp(automation - 18)\n    operations_score = _clamp(task_discipline * 0.7 + management * 0.3)\n''',
        'mandatory process maturity penalties',
    )
    text = once(
        text,
        '    risks: list[dict[str, Any]] = []\n',
        '''    risks: list[dict[str, Any]] = []\n    risks.append({\n        "severity": "critical",\n        "title": "Не внедрены ключевые корпоративные процессы",\n        "fact": "Не реализованы электронный обмен документами, согласование договоров, заявка на создание пользователей в AD и 1С, а также служебные записки",\n        "impact": "Ручная работа, отсутствие прозрачного контроля, единых сроков, истории согласований и персональной ответственности",\n        "priority": 110,\n    })\n''',
        'mandatory capability risk',
    )
    text = once(
        text,
        '    roadmap = {"30_days": [], "60_days": [], "90_days": []}\n',
        '''    roadmap = {"30_days": [], "60_days": [], "90_days": []}\n    roadmap["30_days"].extend([\n        {"title": "Утвердить маршрут согласования договоров", "action": "Определить роли, сроки, замещение, эскалации и правила хранения итоговой версии", "severity": "critical"},\n        {"title": "Утвердить заявку на создание пользователя", "action": "Согласовать единый процесс выдачи доступов в AD и 1С с участием руководителя, кадровой службы и ИТ", "severity": "high"},\n    ])\n    roadmap["60_days"].extend([\n        {"title": "Запустить электронный обмен документами", "action": "Определить типы документов, владельцев, каналы обмена и контроль исполнения", "severity": "high"},\n        {"title": "Запустить служебные записки", "action": "Ввести типовые формы, реестр, маршруты согласования и контроль сроков", "severity": "high"},\n    ])\n''',
        'mandatory capability roadmap',
    )
    text = once(
        text,
        '        "risks": risks,\n',
        '        "risks": risks,\n        "missing_capabilities": missing_capabilities,\n',
        'mandatory capability result',
    )
    EXEC_PATH.write_text(text, encoding='utf-8')

    dash = DASH_PATH.read_text(encoding='utf-8')
    dash = once(
        dash,
        "html+='<div class=\"layout\">",
        "const gaps=d.missing_capabilities||[];html+='<section class=\"section\"><h2>Ключевые процессы, которые не внедрены</h2><p class=\"status\">Это подтверждённые требования компании, а не автоматические предположения системы.</p>'+(gaps.length?gaps.map((x,i)=>'<div class=\"issue\"><div class=\"rank\">'+(i+1)+'</div><div><h3>'+esc(x.title)+'</h3><p><b class=\"bad\">Не реализовано</b> · '+esc(x.area||'')+'</p><p>Последствие: '+esc(x.impact||'')+'</p><p><b>Решение руководства:</b> '+esc(x.decision||'')+'</p></div></div>').join(''):'<div class=\"empty\">Обязательные незавершённые процессы не указаны.</div>')+'</section>';html+='<div class=\"layout\">",
        'mandatory capability dashboard section',
    )
    DASH_PATH.write_text(dash, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH):
        runtime = path.read_text(encoding='utf-8')
        runtime = runtime.replace('1.0.0-rc.14', '1.0.0-rc.15')
        path.write_text(runtime, encoding='utf-8')

    print('Applied AI-BIT mandatory business processes patch 1.0.0-rc.15')


if __name__ == '__main__':
    main()
