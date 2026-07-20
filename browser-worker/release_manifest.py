from __future__ import annotations

from typing import Any

VERSION = "3.1.0"
PRODUCT = "AI-BIT Enterprise"
EDITION = "Readable Linear Design System"
DEVELOPER = "Коваленко А.С."
CONTACT = "pizzakov@gmail.com"


def get_release_manifest() -> dict[str, Any]:
    return {
        "product": PRODUCT,
        "version": VERSION,
        "edition": EDITION,
        "developer": DEVELOPER,
        "contact": CONTACT,
        "copyright": "© 2026 Коваленко А.С. Все права защищены.",
        "principle": "Выводы формируются по подтверждённым данным; неизвестное не считается отсутствующим.",
        "capabilities": [
            "Readable Linear Light Design System",
            "Unified Layout Engine",
            "Compact Executive Report",
            "Bitrix Digital Passport",
            "Executive Intelligence",
            "Management Conclusion",
            "Executive KPI Center",
            "Root Cause Analysis",
            "Advanced Business Value Engine",
            "Reference Model Audit",
            "Knowledge Base & Methodology",
            "Deep REST Evidence",
            "Automatic Capability Discovery",
            "Process Mining",
            "AI Process Optimizer",
            "Roadmap Generator",
            "Executive Timeline",
            "Evidence-Based Risk Forecast",
            "AI CIO",
            "Reports & Export",
            "Scheduling & Automation",
            "System Health & Data Quality",
        ],
        "release_focus": [
            "полностью светлые карточки и контентные блоки без чёрных областей",
            "повышенная контрастность текста, метрик, таблиц и форм",
            "единая спокойная цветовая логика для рисков и статусов",
            "сохранение защиты от вложенного Unified Admin и двойного sidebar",
            "единый читаемый визуальный язык для всех основных дашбордов",
        ],
        "interfaces": {
            "management": "/#management",
            "digital_passport": "/digital-passport",
            "process_optimizer": "/process-optimizer",
            "ai_cio": "/ai-cio",
            "roadmap": "/transformation-roadmap",
            "risk_forecast": "/risk-forecast",
            "business_value": "/business-value",
        },
    }
