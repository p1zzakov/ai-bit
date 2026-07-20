from __future__ import annotations

from typing import Any

VERSION = "3.3.0"
PRODUCT = "AI-BIT Enterprise"
EDITION = "Evidence-Based Executive Decision Intelligence"
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
            "Evidence-Based AI CIO Recommendations",
            "Department Operational Maturity",
            "AI Timeline from Historical Snapshots",
            "Transparent Executive Score",
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
            "Reports & Export",
            "Scheduling & Automation",
            "System Health & Data Quality",
        ],
        "release_focus": [
            "конкретные рекомендации AI CIO только по подтверждённым отклонениям",
            "операционная зрелость подразделений без оценки ценности сотрудников",
            "динамика цифровой зрелости по сохранённым снимкам без прогнозных допущений",
            "прозрачный Executive Score с весами и расшифровкой компонентов",
            "исключение новых финансовых оценок и неподтверждённых предположений",
        ],
        "interfaces": {
            "management": "/#management",
            "executive_intelligence": "/#intelligence",
            "digital_passport": "/digital-passport",
            "process_optimizer": "/process-optimizer",
            "ai_cio": "/ai-cio",
            "roadmap": "/transformation-roadmap",
            "risk_forecast": "/risk-forecast",
            "business_value": "/business-value",
        },
    }
