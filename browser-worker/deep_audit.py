from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

MODULE_PLAYBOOK: dict[str, dict[str, Any]] = {
    "crm": {
        "title": "CRM",
        "goal": "Управляемая воронка продаж, единая клиентская база и автоматический контроль следующего действия.",
        "checks": ["воронки и стадии", "обязательные поля", "роботы и триггеры", "дубли", "источники", "зависшие сделки"],
        "recommendations": [
            "Проверить количество и назначение воронок, убрать дублирующие стадии и закрепить владельцев процессов.",
            "Сделать обязательными источник, сумма, ответственное лицо и следующее действие до перехода сделки дальше.",
            "Добавить роботов контроля зависших сделок, уведомления и автоматическое создание задач.",
            "Подключить телефонию, почту и внешние формы так, чтобы обращения автоматически попадали в CRM.",
        ],
    },
    "tasks": {
        "title": "Задачи и проекты",
        "goal": "Прозрачное исполнение поручений со сроками, результатом, ответственностью и контролем просрочки.",
        "checks": ["сроки", "результат", "шаблоны", "повторяемость", "проекты", "эскалации"],
        "recommendations": [
            "Запретить типовые рабочие задачи без срока, исполнителя и ожидаемого результата.",
            "Создать шаблоны и повторяющиеся задачи для регламентных операций.",
            "Ввести автоматическую эскалацию просрочки и отдельный контроль задач без движения.",
            "Разделить сервисные заявки, проекты и личные поручения по отдельным очередям и рабочим группам.",
        ],
    },
    "company": {
        "title": "Структура компании",
        "goal": "Актуальная оргструктура как источник ролей, маршрутов согласования и управленческой аналитики.",
        "checks": ["подразделения", "руководители", "должности", "замещения", "увольнения", "роли"],
        "recommendations": [
            "Сверить структуру Bitrix24 со штатной структурой и назначить владельца актуальности данных.",
            "Использовать подразделения и руководителей в маршрутах согласования вместо ручного выбора сотрудников.",
            "Автоматизировать блокировку и перераспределение объектов при увольнении или переводе сотрудника.",
        ],
    },
    "page": {
        "title": "Цифровые процессы и формы",
        "goal": "Стандартизированные заявки и согласования с владельцем, SLA, статусами и прозрачной историей.",
        "checks": ["владелец", "SLA", "маршрут", "обязательные поля", "уведомления", "результат"],
        "recommendations": [
            "Для каждого процесса определить владельца, SLA, входные данные, результат и правила эскалации.",
            "Автоматически подставлять сотрудника, подразделение и руководителя из оргструктуры.",
            "Убирать ручные дублирующиеся поля и заменять их справочниками или интеграциями.",
            "Добавить уведомление заявителя и контроль зависших согласований.",
        ],
    },
    "groups": {
        "title": "Рабочие группы",
        "goal": "Разделение проектных контекстов, документов, задач и участников.",
        "checks": ["владелец", "архивация", "права", "задачи", "документы"],
        "recommendations": [
            "Определить правила создания, именования и архивирования рабочих групп.",
            "Назначить владельца и резервного владельца каждой активной группы.",
            "Не хранить проектные задачи и документы вне соответствующей рабочей группы.",
        ],
    },
    "disk": {
        "title": "Документы и диск",
        "goal": "Единое контролируемое хранение рабочих документов с понятными правами и версиями.",
        "checks": ["структура папок", "права", "версии", "дубли", "владельцы"],
        "recommendations": [
            "Утвердить структуру общих папок и матрицу доступа по подразделениям.",
            "Убрать персональные ссылки как основной механизм доступа к корпоративным документам.",
            "Настроить правила версий, архивирования и удаления устаревших документов.",
        ],
    },
    "calendar": {
        "title": "Календарь",
        "goal": "Единое планирование встреч, ресурсов и обязательных мероприятий.",
        "checks": ["общие календари", "переговорные", "ресурсы", "напоминания", "занятость"],
        "recommendations": [
            "Создать общие календари подразделений и ресурсов, включая переговорные и оборудование.",
            "Использовать занятость участников при назначении встреч и автоматические напоминания.",
        ],
    },
    "knowledge": {
        "title": "База знаний",
        "goal": "Актуальные регламенты и инструкции, не зависящие от отдельных сотрудников.",
        "checks": ["владельцы", "актуальность", "поиск", "структура", "доступ"],
        "recommendations": [
            "Назначить владельца и срок пересмотра для каждого раздела базы знаний.",
            "Разделить регламенты, инструкции и ответы на частые вопросы.",
            "Связать типовые задачи и процессы с соответствующими инструкциями.",
        ],
    },
    "rpa": {
        "title": "RPA",
        "goal": "Автоматизация нестандартных внутренних процессов с измеримыми статусами и SLA.",
        "checks": ["стадии", "роботы", "SLA", "владельцы", "аналитика"],
        "recommendations": [
            "Использовать RPA только для процессов с чёткими стадиями, владельцем и измеримым результатом.",
            "Настроить роботов, контроль времени в стадии и отчёт по узким местам.",
        ],
    },
}

GENERIC_RECOMMENDATIONS = {
    "denied": "Проверить права технической учётной записи и матрицу доступа. Недоступность не должна скрывать состояние критичного процесса.",
    "not_found": "Проверить корректность маршрута, наличие модуля и актуальность ссылки в меню или процессе.",
    "partial": "Страница загружается не полностью. Проверить ошибки frontend, долгие запросы, PHP и сторонние интеграции.",
    "redirected": "Проверить назначение перенаправления и убедиться, что пользователь попадает в ожидаемый рабочий сценарий.",
    "error": "Устранить техническую ошибку страницы и повторить аудит после исправления.",
}


def _risk_for_status(status: str) -> str:
    if status in {"denied", "not_found", "error"}:
        return "high"
    if status in {"partial", "redirected"}:
        return "medium"
    return "low"


def _page_recommendations(node: dict[str, Any]) -> list[str]:
    status = str(node.get("status") or "error")
    section = str(node.get("section") or "other")
    title = str(node.get("title") or "").strip()
    text = str(node.get("text_sample") or "").lower()
    link_count = int(node.get("link_count") or 0)
    recs: list[str] = []
    if status in GENERIC_RECOMMENDATIONS:
        recs.append(GENERIC_RECOMMENDATIONS[status])
    if status == "ok" and not title:
        recs.append("Добавить понятный заголовок страницы, чтобы назначение раздела было очевидно пользователям и в отчётности.")
    if status == "ok" and link_count == 0:
        recs.append("Проверить навигацию и следующий шаг пользователя: страница выглядит изолированной от рабочего процесса.")
    if section == "page":
        if not any(word in text for word in ("срок", "sla", "дедлайн")):
            recs.append("Зафиксировать срок обработки или SLA и правила эскалации для этой заявки.")
        if not any(word in text for word in ("ответствен", "исполнитель", "соглас")):
            recs.append("Определить владельца процесса и ответственных на каждой стадии.")
        if not any(word in text for word in ("статус", "этап", "стад")):
            recs.append("Добавить понятные статусы процесса и уведомление заявителя при их изменении.")
    elif section == "crm":
        recs.append("Проверить обязательные поля, автоматизацию следующего действия и контроль зависших элементов на этой странице CRM.")
    elif section == "tasks":
        recs.append("Проверить наличие срока, ожидаемого результата, проекта и правил эскалации просрочки.")
    elif section == "company":
        recs.append("Проверить соответствие данных штатной структуре и использование подразделения в правах и согласованиях.")
    elif section == "disk":
        recs.append("Проверить владельца документов, матрицу доступа, версии и правила архивирования.")
    return list(dict.fromkeys(recs))[:4]


def analyze_deep_audit(crawl: dict[str, Any]) -> dict[str, Any]:
    nodes = list(crawl.get("nodes") or [])
    by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    page_findings: list[dict[str, Any]] = []

    for node in nodes:
        section = str(node.get("section") or "other")
        by_section[section].append(node)
        recs = _page_recommendations(node)
        page_findings.append({
            "url": node.get("url"),
            "title": node.get("title") or node.get("url"),
            "section": section,
            "status": node.get("status"),
            "http_status": node.get("http_status"),
            "risk": _risk_for_status(str(node.get("status") or "error")),
            "evidence": {
                "link_count": node.get("link_count", 0),
                "depth": node.get("depth", 0),
                "text_sample": str(node.get("text_sample") or "")[:400],
            },
            "recommendations": recs,
        })

    module_findings: list[dict[str, Any]] = []
    action_plan: list[dict[str, Any]] = []
    for key, playbook in MODULE_PLAYBOOK.items():
        pages = by_section.get(key, [])
        statuses = Counter(str(p.get("status") or "error") for p in pages)
        healthy = sum(statuses[s] for s in ("ok", "redirected"))
        unhealthy = len(pages) - healthy
        if not pages:
            maturity = "not_detected"
            score = 0
        elif unhealthy:
            maturity = "at_risk"
            score = max(20, round(healthy * 100 / len(pages)))
        else:
            maturity = "detected"
            score = 70
        module_recs = list(playbook["recommendations"])
        if unhealthy:
            module_recs.insert(0, f"Сначала устранить {unhealthy} технически проблемных страниц модуля.")
        module = {
            "key": key,
            "title": playbook["title"],
            "goal": playbook["goal"],
            "maturity": maturity,
            "score": score,
            "pages": len(pages),
            "healthy_pages": healthy,
            "problem_pages": unhealthy,
            "status_counts": dict(statuses),
            "checks": playbook["checks"],
            "recommendations": module_recs,
            "evidence": [{"title": p.get("title"), "url": p.get("url"), "status": p.get("status")} for p in pages[:8]],
        }
        module_findings.append(module)
        if maturity != "detected" or unhealthy:
            priority = "high" if key in {"crm", "tasks", "company", "page"} else "medium"
            action_plan.append({
                "priority": priority,
                "module": key,
                "title": playbook["title"],
                "action": module_recs[0],
                "expected_effect": playbook["goal"],
            })

    page_findings.sort(key=lambda x: ({"high": 0, "medium": 1, "low": 2}[x["risk"]], x["section"], str(x["title"])))
    action_plan.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])
    problem_pages = [p for p in page_findings if p["risk"] != "low"]
    recommended_pages = [p for p in page_findings if p["recommendations"]]

    return {
        "version": "0.8.0",
        "summary": {
            "modules_analyzed": len(module_findings),
            "pages_analyzed": len(page_findings),
            "problem_pages": len(problem_pages),
            "pages_with_recommendations": len(recommended_pages),
            "high_priority_actions": sum(1 for x in action_plan if x["priority"] == "high"),
        },
        "modules": module_findings,
        "pages": page_findings,
        "action_plan": action_plan,
        "methodology": "Экспертная эвристика по browser evidence. Для оценки воронок, полей, роботов, задач и пользовательской эффективности требуется объединение с REST snapshot.",
    }
