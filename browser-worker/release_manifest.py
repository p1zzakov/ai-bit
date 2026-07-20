from __future__ import annotations

from typing import Any

VERSION = "2.1.0"
PRODUCT = "AI-BIT Enterprise"
EDITION = "Intelligent Transformation Suite"
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
            "единая управленческая сводка без обязательной зависимости от LLM",
            "доказательный аудит Bitrix24",
            "оптимизация процессов и поиск узких мест",
            "экономическое обоснование цифровой трансформации",
            "дорожная карта и приоритеты для руководства",
        ],
    }
