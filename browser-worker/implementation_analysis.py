from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

IDEAL_MODULES: dict[str, dict[str, Any]] = {
    "crm": {"title": "CRM", "priority": "critical", "why": "Единый контур продаж, клиентов и контроля воронки."},
    "tasks": {"title": "Задачи и проекты", "priority": "critical", "why": "Управление исполнением, сроками и ответственностью."},
    "company": {"title": "Структура компании", "priority": "critical", "why": "Основа маршрутов согласования, ролей и доступа."},
    "page": {"title": "Цифровые процессы и формы", "priority": "critical", "why": "Автоматизация внутренних заявок и согласований."},
    "groups": {"title": "Рабочие группы", "priority": "recommended", "why": "Проектная работа и разделение контекстов."},
    "disk": {"title": "Документы и диск", "priority": "recommended", "why": "Централизованное хранение рабочих документов."},
    "calendar": {"title": "Календарь", "priority": "recommended", "why": "Планирование встреч, ресурсов и событий."},
    "knowledge": {"title": "База знаний", "priority": "recommended", "why": "Снижение зависимости от отдельных сотрудников."},
    "contact_center": {"title": "Контакт-центр", "priority": "optional", "why": "Омниканальные коммуникации с клиентами."},
    "openlines": {"title": "Открытые линии", "priority": "optional", "why": "Управляемые клиентские диалоги и статистика."},
    "rpa": {"title": "RPA", "priority": "optional", "why": "Автоматизация нестандартных процессов."},
    "marketing": {"title": "Маркетинг", "priority": "optional", "why": "Сегментация и маркетинговые кампании."},
    "bi": {"title": "BI-аналитика", "priority": "recommended", "why": "Управленческая отчётность и контроль KPI."},
    "mail": {"title": "Почта", "priority": "recommended", "why": "Связь переписки с задачами и CRM."},
    "market": {"title": "Маркетплейс и интеграции", "priority": "recommended", "why": "Расширение функциональности и интеграции."},
    "devops": {"title": "Инструменты разработчика", "priority": "optional", "why": "Управление интеграциями и кастомной разработкой."},
    "booking": {"title": "Онлайн-запись", "priority": "optional", "why": "Управление бронированиями и ресурсами."},
}

STATUS_WEIGHT = {"ok": 1.0, "redirected": 0.9, "partial": 0.55, "denied": 0.15, "not_found": 0.0, "error": 0.0}
PRIORITY_WEIGHT = {"critical": 3, "recommended": 2, "optional": 1}


def analyze_implementation(crawl: dict[str, Any]) -> dict[str, Any]:
    nodes = crawl.get("nodes") or []
    by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        by_section[str(node.get("section") or "other")].append(node)

    modules: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    total_weight = 0.0
    earned = 0.0

    for key, ideal in IDEAL_MODULES.items():
        pages = by_section.get(key, [])
        statuses = Counter(str(page.get("status") or "error") for page in pages)
        detected = bool(pages)
        best = max((STATUS_WEIGHT.get(str(page.get("status")), 0.0) for page in pages), default=0.0)
        weight = PRIORITY_WEIGHT[ideal["priority"]]
        total_weight += weight
        earned += best * weight

        if not detected:
            state = "not_detected"
            recommendation = f"Проверить необходимость модуля «{ideal['title']}» и включить его в целевую модель внедрения."
        elif best < 0.5:
            state = "blocked"
            recommendation = f"Восстановить доступ и базовую работоспособность модуля «{ideal['title']}»."
        elif best < 0.8:
            state = "needs_configuration"
            recommendation = f"Донастроить «{ideal['title']}»: проверить права, сценарии использования, владельца и регламент."
        else:
            state = "used"
            recommendation = ""

        module = {
            "key": key,
            "title": ideal["title"],
            "priority": ideal["priority"],
            "why": ideal["why"],
            "state": state,
            "pages": len(pages),
            "status_counts": dict(statuses),
            "sample_pages": [{"title": p.get("title"), "url": p.get("url"), "status": p.get("status")} for p in pages[:5]],
        }
        modules.append(module)

        if recommendation:
            severity = "high" if ideal["priority"] == "critical" else "medium" if ideal["priority"] == "recommended" else "low"
            recommendations.append({
                "module": key,
                "title": ideal["title"],
                "severity": severity,
                "state": state,
                "recommendation": recommendation,
                "business_value": ideal["why"],
            })

    unknown = sorted(key for key in by_section if key not in IDEAL_MODULES and key not in {"home", "other"})
    used = [m for m in modules if m["state"] == "used"]
    needs = [m for m in modules if m["state"] == "needs_configuration"]
    blocked = [m for m in modules if m["state"] == "blocked"]
    missing = [m for m in modules if m["state"] == "not_detected"]
    score = round(earned * 100 / total_weight) if total_weight else 0

    return {
        "implementation_score": score,
        "maturity": "advanced" if score >= 80 else "managed" if score >= 60 else "developing" if score >= 35 else "initial",
        "counts": {
            "used": len(used),
            "needs_configuration": len(needs),
            "blocked": len(blocked),
            "not_detected": len(missing),
            "discovered_pages": len(nodes),
            "custom_sections": len(unknown),
        },
        "modules": modules,
        "used": used,
        "needs_configuration": needs,
        "blocked": blocked,
        "not_detected": missing,
        "custom_sections": unknown,
        "recommendations": sorted(recommendations, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]]),
        "disclaimer": "Оценка эвристическая: она сравнивает обнаруженную конфигурацию с типовой целевой моделью и требует подтверждения владельцами процессов.",
    }
