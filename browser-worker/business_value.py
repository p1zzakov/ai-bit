from __future__ import annotations

import os
from typing import Any

VERSION = "2.0.0-alpha.8"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_business_value(result: dict[str, Any]) -> dict[str, Any]:
    roi = result.get("roi") or {}
    source = result.get("source_summary") or {}

    hourly_rate = _num(roi.get("hourly_cost_kzt") or os.getenv("ROI_HOURLY_COST_KZT"), 0)
    labor_hours = _num(roi.get("total_annual_hours"), 0)
    labor_saving = _num(roi.get("total_annual_saving_kzt"), 0)

    active_users = max(1, int(_num(source.get("active_users") or source.get("users"), 0) or 1))

    # Усреднённая методика AI-BIT для бумажного документооборота.
    # Учитываются бумага, тонер, ресурс печати и сопутствующие расходы.
    pages_per_user_month = _num(os.getenv("PAPER_PAGES_PER_USER_MONTH"), 25)
    blended_page_cost_kzt = _num(os.getenv("PAPER_BLENDED_PAGE_COST_KZT"), 15)
    expected_reduction_rate = _num(os.getenv("PAPER_REDUCTION_RATE"), 0.60)
    expected_reduction_rate = max(0.0, min(1.0, expected_reduction_rate))

    annual_pages_before = round(active_users * pages_per_user_month * 12)
    annual_pages_avoided = round(annual_pages_before * expected_reduction_rate)
    paper_saving = round(annual_pages_avoided * blended_page_cost_kzt)
    total_saving = round(labor_saving + paper_saving)

    return {
        "version": VERSION,
        "labor": {
            "annual_hours": round(labor_hours, 1),
            "hourly_rate_kzt": round(hourly_rate, 2) if hourly_rate > 0 else None,
            "annual_saving_kzt": round(labor_saving) if labor_saving > 0 else None,
            "calculation_note": (
                f"Расчёт выполнен по средней стоимости рабочего часа {hourly_rate:,.0f} ₸."
                .replace(",", " ")
                if hourly_rate > 0
                else "Средняя стоимость рабочего часа не задана."
            ),
        },
        "paper": {
            "method": "average_scenario",
            "active_users": active_users,
            "pages_per_user_month": pages_per_user_month,
            "blended_page_cost_kzt": blended_page_cost_kzt,
            "expected_reduction_rate": expected_reduction_rate,
            "annual_pages_before": annual_pages_before,
            "annual_pages_avoided": annual_pages_avoided,
            "annual_saving_kzt": paper_saving,
            "calculation_note": (
                "Ориентировочная экономия после внедрения электронного документооборота. "
                f"Использован средний сценарий: {pages_per_user_month:g} страниц на пользователя в месяц, "
                f"совокупная стоимость страницы {blended_page_cost_kzt:g} ₸ и сокращение печати на "
                f"{expected_reduction_rate * 100:.0f}%."
            ),
            "included_costs": [
                "бумага",
                "тонер и картриджи",
                "ресурс печатающей техники",
                "сопутствующие расходы на печать",
            ],
        },
        "total": {
            "annual_saving_kzt": total_saving,
            "calculation_note": "Совокупный ориентировочный эффект включает экономию рабочего времени и сокращение расходов на бумажный документооборот.",
        },
        "disclaimer": "Расчёт является прогнозным. Фактический эффект зависит от объёма документов, доли электронной обработки и организационной дисциплины.",
    }
