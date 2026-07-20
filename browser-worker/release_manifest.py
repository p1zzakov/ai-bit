from __future__ import annotations

from typing import Any

VERSION = "3.2.1"
PRODUCT = "AI-BIT Enterprise"
EDITION = "Automation History Readability Fix"
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
            "Complete Readable Linear Light UI",
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
            "светлый и читаемый журнал запусков Scheduling & Automation",
            "белые карточки событий с нейтральными границами и hover-состоянием",
            "контрастные статусы ok, error и running без тёмных плашек",
            "сохранение единой Linear-дизайн-системы и защиты от двойного sidebar",
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
