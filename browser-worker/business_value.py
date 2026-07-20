from __future__ import annotations

import os
from typing import Any

VERSION = "2.0.0-alpha.9"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _money(value: float) -> int:
    return max(0, round(value))


def build_business_value(result: dict[str, Any]) -> dict[str, Any]:
    roi = result.get("roi") or {}
    source = result.get("source_summary") or {}
    reference = result.get("reference_audit") or {}
    departments = result.get("department_rating") or []

    hourly_rate = _num(roi.get("hourly_cost_kzt") or os.getenv("ROI_HOURLY_COST_KZT"), 0)
    labor_hours = _num(roi.get("total_annual_hours"), 0)
    labor_saving = _num(roi.get("total_annual_saving_kzt"), 0)
    if labor_saving <= 0 and hourly_rate > 0:
        labor_saving = labor_hours * hourly_rate

    active_users = max(1, int(_num(source.get("active_users") or source.get("users"), 0) or 1))
    open_tasks = max(0, int(_num(source.get("open"), 0)))
    overdue_count = max(0, int(_num(source.get("overdue"), 0)))
    overdue_rate = max(0.0, _num(source.get("overdue_rate"), 0))
    without_deadline = max(0, int(_num(source.get("without_deadline"), 0)))
    if overdue_count == 0 and open_tasks > 0 and overdue_rate > 0:
        overdue_count = round(open_tasks * overdue_rate / 100)

    # Бумага и печать: усреднённый сценарий AI-BIT.
    pages_per_user_month = _num(os.getenv("PAPER_PAGES_PER_USER_MONTH"), 25)
    blended_page_cost_kzt = _num(os.getenv("PAPER_BLENDED_PAGE_COST_KZT"), 15)
    paper_reduction_rate = max(0.0, min(1.0, _num(os.getenv("PAPER_REDUCTION_RATE"), 0.60)))
    annual_pages_before = round(active_users * pages_per_user_month * 12)
    annual_pages_avoided = round(annual_pages_before * paper_reduction_rate)
    paper_saving = _money(annual_pages_avoided * blended_page_cost_kzt)

    # Потери от просрочки: 30 минут дополнительной координации на одну просроченную задачу в месяц.
    overdue_minutes_per_task_month = _num(os.getenv("VALUE_OVERDUE_MINUTES_PER_TASK_MONTH"), 30)
    overdue_hours = overdue_count * overdue_minutes_per_task_month / 60 * 12
    overdue_loss = _money(overdue_hours * hourly_rate) if hourly_rate > 0 else 0

    # Задачи без срока: 15 минут дополнительного контроля на задачу в месяц.
    no_deadline_minutes_per_task_month = _num(os.getenv("VALUE_NO_DEADLINE_MINUTES_PER_TASK_MONTH"), 15)
    no_deadline_hours = without_deadline * no_deadline_minutes_per_task_month / 60 * 12
    no_deadline_loss = _money(no_deadline_hours * hourly_rate) if hourly_rate > 0 else 0

    # Поиск документов: 30 минут на активного пользователя в месяц можно сократить единым реестром и поиском.
    document_search_hours_per_user_month = _num(os.getenv("VALUE_DOCUMENT_SEARCH_HOURS_USER_MONTH"), 0.5)
    document_search_hours = active_users * document_search_hours_per_user_month * 12
    document_search_saving = _money(document_search_hours * hourly_rate) if hourly_rate > 0 else 0

    # Время руководителей: 1.5 часа в месяц на подразделение на ручной сбор статусов и контроль.
    meaningful_departments = [row for row in departments if _num(row.get("open"), 0) >= 3]
    department_count = max(1, len(meaningful_departments))
    management_hours_department_month = _num(os.getenv("VALUE_MANAGEMENT_HOURS_DEPARTMENT_MONTH"), 1.5)
    management_hours = department_count * management_hours_department_month * 12
    management_saving = _money(management_hours * hourly_rate) if hourly_rate > 0 else 0

    # Согласования: эффект показывается в часах/процентах и не включается повторно в денежный итог.
    approval_reduction_rate = max(0.0, min(1.0, _num(os.getenv("VALUE_APPROVAL_REDUCTION_RATE"), 0.50)))

    # Неиспользуемый потенциал — индикатор масштаба возможности, а не гарантированная экономия.
    coverage = max(0.0, min(100.0, _num(reference.get("coverage"), 0)))
    unused_share = max(0.0, (100.0 - coverage) / 100.0)
    proven_annual_base = labor_saving + paper_saving + overdue_loss + no_deadline_loss + document_search_saving + management_saving
    unused_potential_value = _money(proven_annual_base * unused_share)

    # Не складываем исходную автоматизацию повторно с потерями, если они описывают один и тот же труд.
    # Общий прогноз — сумма независимых консервативных блоков.
    total_saving = _money(
        labor_saving
        + paper_saving
        + overdue_loss
        + no_deadline_loss
        + document_search_saving
        + management_saving
    )
    total_hours = round(
        labor_hours + overdue_hours + no_deadline_hours + document_search_hours + management_hours,
        1,
    )

    return {
        "version": VERSION,
        "labor": {
            "annual_hours": round(labor_hours, 1),
            "hourly_rate_kzt": round(hourly_rate, 2) if hourly_rate > 0 else None,
            "annual_saving_kzt": _money(labor_saving) if labor_saving > 0 else None,
            "calculation_note": (
                f"Расчёт выполнен по средней стоимости рабочего часа {hourly_rate:,.0f} ₸.".replace(",", " ")
                if hourly_rate > 0 else "Средняя стоимость рабочего часа не задана."
            ),
        },
        "paper": {
            "method": "average_scenario",
            "active_users": active_users,
            "pages_per_user_month": pages_per_user_month,
            "blended_page_cost_kzt": blended_page_cost_kzt,
            "expected_reduction_rate": paper_reduction_rate,
            "annual_pages_before": annual_pages_before,
            "annual_pages_avoided": annual_pages_avoided,
            "annual_saving_kzt": paper_saving,
            "calculation_note": (
                "Усреднённый сценарий AI-BIT: "
                f"{pages_per_user_month:g} страниц на пользователя в месяц, стоимость страницы "
                f"{blended_page_cost_kzt:g} ₸, сокращение печати на {paper_reduction_rate * 100:.0f}%."
            ),
            "included_costs": ["бумага", "тонер и картриджи", "ресурс печатающей техники", "архивирование и сопутствующая печать"],
        },
        "management_time": {
            "departments": department_count,
            "annual_hours": round(management_hours, 1),
            "annual_saving_kzt": management_saving if hourly_rate > 0 else None,
            "calculation_note": f"Средний сценарий: {management_hours_department_month:g} часа ручного сбора статусов на подразделение в месяц.",
        },
        "overdue_losses": {
            "overdue_tasks": overdue_count,
            "annual_hours": round(overdue_hours, 1),
            "annual_loss_kzt": overdue_loss if hourly_rate > 0 else None,
            "calculation_note": f"Консервативно учтено {overdue_minutes_per_task_month:g} минут дополнительной координации на одну просроченную задачу в месяц.",
        },
        "no_deadline_losses": {
            "tasks_without_deadline": without_deadline,
            "annual_hours": round(no_deadline_hours, 1),
            "annual_loss_kzt": no_deadline_loss if hourly_rate > 0 else None,
            "calculation_note": f"Консервативно учтено {no_deadline_minutes_per_task_month:g} минут дополнительного контроля на задачу без срока в месяц.",
        },
        "document_search": {
            "annual_hours": round(document_search_hours, 1),
            "annual_saving_kzt": document_search_saving if hourly_rate > 0 else None,
            "calculation_note": f"Средний сценарий: сокращение поиска документов на {document_search_hours_per_user_month:g} часа на пользователя в месяц.",
        },
        "approvals": {
            "expected_cycle_reduction_rate": approval_reduction_rate,
            "calculation_note": f"После стандартизации маршрутов ожидаемое сокращение длительности согласований — до {approval_reduction_rate * 100:.0f}%.",
            "included_in_total": False,
        },
        "unused_potential": {
            "reference_coverage": round(coverage, 1),
            "unused_share": round(unused_share, 3),
            "indicative_value_kzt": unused_potential_value if hourly_rate > 0 else None,
            "calculation_note": "Индикативная стоимость неиспользуемого потенциала рассчитана пропорционально разрыву эталонной модели и не включена в совокупный итог, чтобы избежать двойного счёта.",
        },
        "total": {
            "annual_hours": total_hours,
            "annual_saving_kzt": total_saving if hourly_rate > 0 else paper_saving,
            "included_components": ["автоматизация повторяющихся операций", "бумага и печать", "контроль просрочки", "задачи без срока", "поиск документов", "время руководителей"],
            "calculation_note": "Совокупный прогноз рассчитан как сумма независимых консервативных компонентов. Ускорение согласований и неиспользуемый потенциал показываются отдельно и не прибавляются повторно.",
        },
        "disclaimer": "Расчёт является прогнозным и предназначен для приоритизации. Фактический эффект зависит от объёма операций, качества регламентов и дисциплины исполнения.",
    }
