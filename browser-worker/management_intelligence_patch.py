from __future__ import annotations

from pathlib import Path

MANAGEMENT_PATH = Path('/app/management_report.py')
APP_PATH = Path('/app/app.py')
ADMIN_PATH = Path('/app/admin_dashboard.py')


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


def main() -> None:
    text = MANAGEMENT_PATH.read_text(encoding='utf-8')
    text = text.replace('VERSION = "1.0.0-rc.10"', 'VERSION = "1.0.0-rc.12"')
    text = once(
        text,
        'from playwright.async_api import async_playwright',
        'from playwright.async_api import async_playwright\n\nfrom executive_intelligence import build_executive_intelligence',
        'executive intelligence import',
    )
    text = once(
        text,
        '    mining = _read(root / "process-mining" / "latest.json")\n    assessment = crawl.get("assessment") or {}',
        '    mining = _read(root / "process-mining" / "latest.json")\n    # Recalculate the executive layer before every management report so Groq\n    # receives the latest maturity, risks, department rating, ROI and roadmap.\n    intelligence = build_executive_intelligence(root)\n    assessment = crawl.get("assessment") or {}',
        'fresh executive intelligence context',
    )
    text = once(
        text,
        '        "deep_audit": {\n            "summary": deep.get("summary", {}),\n            "action_plan": deep.get("action_plan", [])[:20],\n        },',
        '        "executive_intelligence": {\n            "digital_maturity": intelligence.get("digital_maturity", {}),\n            "dimensions": intelligence.get("dimensions", {}),\n            "risks": intelligence.get("risks", [])[:15],\n            "department_rating": intelligence.get("department_rating", [])[:20],\n            "executive_feed": intelligence.get("executive_feed", [])[:12],\n            "roi": intelligence.get("roi", {}),\n            "roadmap": intelligence.get("roadmap", {}),\n            "source_summary": intelligence.get("source_summary", {}),\n        },\n        "deep_audit": {\n            "summary": deep.get("summary", {}),\n            "action_plan": deep.get("action_plan", [])[:20],\n        },',
        'executive intelligence management context',
    )
    text = once(
        text,
        'Не оценивай личности сотрудников. Оценивай организацию работы, контроль, нагрузку, процессы и качество управления.\nВерни строго JSON со структурой:',
        'Не оценивай личности сотрудников. Оценивай организацию работы, контроль, нагрузку, процессы и качество управления.\nОбязательно используй блок executive_intelligence: объясни уровень цифровой зрелости, главные риски, проблемные подразделения, потенциал автоматизации, возможный экономический эффект и дорожную карту. Не называй внутренние технические названия полей. Если денежный ROI не рассчитан, говори только об экономии рабочего времени.\nВерни строго JSON со структурой:',
        'management prompt intelligence instruction',
    )
    text = once(
        text,
        '  "overall_assessment": "связное общее заключение",\n  "strengths":',
        '  "overall_assessment": "связное общее заключение с учётом уровня цифровой зрелости",\n  "digital_maturity_summary": "простое объяснение уровня цифровой зрелости и главных факторов оценки",\n  "strengths":',
        'digital maturity output field',
    )
    text = once(
        text,
        '  "top_priorities": ["конкретное действие в порядке приоритета"],\n  "plan":',
        '  "top_priorities": ["конкретное действие в порядке приоритета"],\n  "expected_effect": {{"time_saving":"оценка экономии времени или недостаточно данных","financial_effect":"денежный эффект либо пояснение, что методика не задана"}},\n  "plan":',
        'expected effect output field',
    )
    text = once(
        text,
        '<section><h2>Общая оценка</h2><div class="lead">{escape(str(report.get("overall_assessment", "")))}</div></section>',
        '<section><h2>Общая оценка</h2><div class="lead">{escape(str(report.get("overall_assessment", "")))}</div></section>\n<section><h2>Цифровая зрелость</h2><p>{escape(str(report.get("digital_maturity_summary", "Данных для оценки недостаточно.")))}</p></section>',
        'digital maturity html section',
    )
    text = once(
        text,
        '<section><h2>Что сделать в первую очередь</h2>{_render_list(report.get("top_priorities", []))}</section>',
        '<section><h2>Что сделать в первую очередь</h2>{_render_list(report.get("top_priorities", []))}</section>\n<section><h2>Ожидаемый эффект</h2><p><b>Экономия времени:</b> {escape(str((report.get("expected_effect") or {}).get("time_saving", "Данных недостаточно.")))}</p><p><b>Экономический эффект:</b> {escape(str((report.get("expected_effect") or {}).get("financial_effect", "Методика не задана.")))}</p></section>',
        'expected effect html section',
    )
    MANAGEMENT_PATH.write_text(text, encoding='utf-8')

    for path in (APP_PATH, ADMIN_PATH):
        runtime = path.read_text(encoding='utf-8')
        runtime = runtime.replace('1.0.0-rc.11', '1.0.0-rc.12')
        path.write_text(runtime, encoding='utf-8')

    print('Applied AI-BIT Management + Executive Intelligence integration 1.0.0-rc.12')


if __name__ == '__main__':
    main()
