from __future__ import annotations

from typing import Any

VERSION = "2.0.0-alpha.10"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _level(score: float) -> str:
    if score >= 80:
        return "good"
    if score >= 60:
        return "attention"
    return "critical"


def _kpi(key: str, title: str, score: float, explanation: str) -> dict[str, Any]:
    value = _clamp(score)
    return {
        "id": key,
        "title": title,
        "score": value,
        "level": _level(value),
        "explanation": explanation,
    }


def build_executive_kpi(result: dict[str, Any]) -> dict[str, Any]:
    source = result.get("source_summary") or {}
    maturity = result.get("digital_maturity") or {}
    dimensions = result.get("dimensions") or {}
    reference = result.get("reference_audit") or {}
    ref_summary = reference.get("summary") or {}
    business_value = result.get("business_value") or {}

    overdue_rate = _num(source.get("overdue_rate"))
    without_deadline = _num(source.get("without_deadline"))
    open_tasks = max(1.0, _num(source.get("open"), 1))
    employees_at_risk = _num(source.get("employees_at_risk"))
    active_users = max(1.0, _num(source.get("active_users") or source.get("users"), 1))
    coverage = _num(reference.get("coverage"))
    missing = _num(ref_summary.get("missing"))
    partial = _num(ref_summary.get("partial"))

    implementation = _num((dimensions.get("implementation") or {}).get("score"), _num(maturity.get("score")))
    processes = _num((dimensions.get("processes") or {}).get("score"), 50)
    crm = _num((dimensions.get("crm") or {}).get("score"), 50)
    documents = _num((dimensions.get("documents") or {}).get("score"), 50)
    automation = _num((dimensions.get("automation") or {}).get("score"), 50)

    deadline_share = without_deadline / open_tasks * 100
    risk_share = employees_at_risk / active_users * 100
    execution = _clamp(100 - overdue_rate * 2.2 - deadline_share * 0.8)
    management = _clamp(execution * 0.65 + (100 - risk_share) * 0.35)
    usage = _clamp((implementation + coverage + processes + crm + documents + automation) / 6)
    digitalization = _clamp((usage * 0.45) + (management * 0.25) + (execution * 0.30))

    kpis = [
        _kpi("digitalization", "Общий индекс цифровизации", digitalization, "Сводная оценка внедрения, использования, процессов и исполнительской дисциплины."),
        _kpi("implementation", "Зрелость внедрения", implementation, "Насколько полно базовые возможности Bitrix24 введены в эксплуатацию."),
        _kpi("usage", "Эффективность использования", usage, "Насколько фактическое использование соответствует доступному потенциалу системы."),
        _kpi("management", "Управленческая дисциплина", management, "Контроль сроков, нагрузки и ответственности руководителей."),
        _kpi("execution", "Исполнительская дисциплина", execution, "Просрочка, задачи без срока и управляемость исполнения."),
        _kpi("automation", "Автоматизация", automation, "Доля процессов, где ручные операции заменены автоматическими сценариями."),
        _kpi("crm", "Качество CRM", crm, "Полнота и качество ведения клиентского контура и воронок."),
        _kpi("documents", "Документооборот", documents, "Зрелость цифрового хранения, маршрутов и контроля документов."),
    ]

    causes: list[dict[str, Any]] = []

    def add_cause(title: str, fact: str, cause: str, impact: str, action: str, priority: int, confidence: int = 90) -> None:
        causes.append({
            "title": title,
            "fact": fact,
            "root_cause": cause,
            "business_impact": impact,
            "recommended_action": action,
            "priority": priority,
            "confidence": confidence,
        })

    if overdue_rate >= 10:
        add_cause(
            "Просроченные задачи",
            f"Просрочено {overdue_rate:.1f}% открытых задач.",
            "Недостаточный регулярный контроль исполнения и отсутствие устойчивой эскалации отклонений.",
            "Сроки поручений смещаются, а незавершённая работа накапливается.",
            "Ввести еженедельный контроль просрочки, владельцев SLA и автоматическую эскалацию.",
            100,
        )
    if without_deadline > 0:
        add_cause(
            "Задачи без срока",
            f"Без крайнего срока остаётся {int(without_deadline)} активных задач.",
            "Срок не закреплён как обязательный атрибут рабочих задач и шаблонов.",
            "Руководство не может объективно контролировать своевременность исполнения.",
            "Сделать срок обязательным в шаблонах, бизнес-процессах и ручной постановке задач.",
            95,
        )
    if coverage < 75:
        add_cause(
            "Неполное покрытие эталонной модели",
            f"Покрытие эталонной модели составляет {coverage:.1f}%; не подтверждено {int(missing)} возможностей, частично реализовано {int(partial)}.",
            "Внедрение развивалось отдельными функциями без единого целевого контура и критериев завершения.",
            "Часть оплаченного потенциала Bitrix24 не используется, а процессы остаются разрозненными.",
            "Утвердить целевую модель, владельцев процессов, сроки и критерии готовности по каждому разрыву.",
            90,
        )
    if automation < 60:
        add_cause(
            "Низкая автоматизация",
            f"Оценка автоматизации составляет {automation:.1f}/100.",
            "Повторяющиеся операции выполняются вручную, а роботы и маршруты используются ограниченно.",
            "Компания теряет рабочее время и зависит от ручного контроля сотрудников.",
            "Начать с процессов с максимальным подтверждённым экономическим эффектом.",
            82,
        )
    if crm < 60:
        add_cause(
            "Недостаточное качество CRM",
            f"Оценка CRM составляет {crm:.1f}/100.",
            "Не сформированы единые обязательные правила ведения сделок, полей и следующего действия.",
            "Снижается прозрачность продаж и достоверность управленческой аналитики.",
            "Утвердить регламент CRM, обязательные поля, контроль сделок без активности и владельцев воронок.",
            80,
        )
    if documents < 60:
        add_cause(
            "Слабый цифровой документооборот",
            f"Оценка документооборота составляет {documents:.1f}/100.",
            "Документы и согласования не объединены в единый контролируемый цифровой маршрут.",
            "Растут сроки поиска, согласования и риск работы с неактуальными версиями.",
            "Сформировать единый реестр документов, маршруты согласования, сроки и историю решений.",
            78,
        )
    if risk_share >= 5:
        add_cause(
            "Перегрузка отдельных сотрудников",
            f"В зоне риска находится {int(employees_at_risk)} сотрудников ({risk_share:.1f}% активных пользователей).",
            "Работа распределена неравномерно, а лимиты незавершённой работы не контролируются.",
            "Возрастает зависимость от отдельных сотрудников и риск срыва сроков.",
            "Перераспределить очередь, определить сервисные потоки и установить лимиты незавершённой работы.",
            75,
        )

    causes.sort(key=lambda item: item["priority"], reverse=True)
    total_value = _num((business_value.get("total") or {}).get("annual_saving_kzt"))

    return {
        "version": VERSION,
        "kpis": kpis,
        "root_causes": causes[:6],
        "priority_actions": [item["recommended_action"] for item in causes[:3]],
        "summary": {
            "critical_kpis": sum(1 for item in kpis if item["level"] == "critical"),
            "attention_kpis": sum(1 for item in kpis if item["level"] == "attention"),
            "good_kpis": sum(1 for item in kpis if item["level"] == "good"),
            "root_causes": len(causes),
            "annual_business_effect_kzt": round(total_value) if total_value > 0 else None,
        },
        "methodology": "Детерминированный анализ подтверждённых показателей AI-BIT; Groq не участвует в расчёте KPI и причин.",
    }
