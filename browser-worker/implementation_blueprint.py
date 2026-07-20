from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from integrator_diagnostics import build_integrator_diagnostics

VERSION = "3.5.1"


def _rest_proposal(issue: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(issue.get(key) or "")
        for key in ("module", "title", "finding", "fix", "object_ref")
    ).lower()
    method = "manual.configuration"
    params: dict[str, Any] = {
        "object": issue.get("object_ref") or "TO_BE_DEFINED",
        "change": issue.get("fix") or "TO_BE_DEFINED",
    }
    note = "Изменение требует ручной настройки или уточнения поддерживаемого REST-метода."

    if any(token in text for token in ("поле", "userfield", "uf_")):
        method = "crm.deal.userfield.add"
        params = {
            "FIELD_NAME": "TO_BE_DEFINED",
            "EDIT_FORM_LABEL": {"ru": issue.get("title") or "Новое поле"},
            "USER_TYPE_ID": "string",
        }
        note = "Метод и тип сущности необходимо подтвердить по объекту аудита."
    elif any(token in text for token in ("воронк", "category", "направлен")):
        method = "crm.category.add"
        params = {"entityTypeId": "TO_BE_DEFINED", "fields": {"name": issue.get("title") or "Новое направление"}}
        note = "entityTypeId и стадии определяются интегратором после согласования архитектуры."
    elif any(token in text for token in ("смарт-процесс", "smart process", "crm.type")):
        method = "crm.type.add"
        params = {"fields": {"title": issue.get("title") or "Новый смарт-процесс"}}
        note = "Схема полей, категорий и прав формируется отдельными шагами."
    elif any(token in text for token in ("бизнес-процесс", "workflow", "bizproc")):
        method = "bizproc.workflow.template.add"
        params = {"DOCUMENT_TYPE": ["crm", "TO_BE_DEFINED", "TO_BE_DEFINED"], "NAME": issue.get("title") or "Новый процесс"}
        note = "Шаблон процесса требует проектирования и не может быть создан только по факту отклонения."
    elif any(token in text for token in ("робот", "automation", "trigger")):
        method = "crm.automation"
        params = {"entity": issue.get("object_ref") or "TO_BE_DEFINED", "configuration": "TO_BE_DESIGNED"}
        note = "Конкретный REST-метод зависит от редакции и доступности automation API."
    elif any(token in text for token in ("задач", "task")):
        method = "tasks.task.update"
        params = {"taskId": "TO_BE_DEFINED", "fields": {"DEADLINE": "TO_BE_DEFINED"}}
        note = "Предложение показывает тип операции; массовое изменение запрещено политикой AI-BIT."
    elif any(token in text for token in ("прав", "permission", "role")):
        method = "manual.permissions.review"
        params = {"scope": issue.get("object_ref") or issue.get("module"), "target_state": issue.get("fix")}
        note = "Изменение прав должно выполняться вручную после согласования матрицы доступа."

    return {
        "mode": "proposal_only",
        "method": method,
        "params": params,
        "note": note,
        "executed": False,
        "source_issue_id": issue.get("id"),
    }


def build_implementation_blueprint(artifacts_dir: Path) -> dict[str, Any]:
    audit = build_integrator_diagnostics(artifacts_dir)
    issues = [row for row in audit.get("issues", []) if isinstance(row, dict)]
    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda row: (priority_rank.get(str(row.get("severity")), 9), str(row.get("module")), str(row.get("title"))))

    phases: list[dict[str, Any]] = []
    phase_map = {
        "critical": (1, "Стабилизация и блокирующие ошибки"),
        "high": (2, "Критичные доработки конфигурации"),
        "medium": (3, "Функциональные улучшения"),
        "low": (4, "Оптимизация и технический долг"),
    }
    for severity in ("critical", "high", "medium", "low"):
        rows = [row for row in issues if row.get("severity") == severity]
        if not rows:
            continue
        number, name = phase_map[severity]
        phases.append({
            "phase": number,
            "name": name,
            "severity": severity,
            "dependencies": ["Подтвердить объект и evidence", "Согласовать целевую конфигурацию", "Подготовить резервный план"],
            "steps": [
                {
                    "order": index + 1,
                    "issue_id": row.get("id"),
                    "module": row.get("module"),
                    "object_ref": row.get("object_ref"),
                    "task": row.get("fix"),
                    "basis": row.get("finding"),
                    "acceptance": row.get("verification"),
                    "rest": _rest_proposal(row),
                }
                for index, row in enumerate(rows)
            ],
        })

    specification = [
        {
            "number": index + 1,
            "module": row.get("module"),
            "severity": row.get("severity"),
            "object_ref": row.get("object_ref"),
            "requirement": row.get("fix"),
            "basis": row.get("finding"),
            "evidence": row.get("evidence") or [],
            "acceptance": row.get("verification"),
            "source": row.get("source"),
        }
        for index, row in enumerate(issues)
    ]

    return {
        "version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "read_only",
        "execution_policy": {
            "rest_execution": False,
            "write_operations": False,
            "automatic_changes": False,
            "description": "AI-BIT формирует только проект изменений. REST-запросы не отправляются и данные Bitrix24 не изменяются.",
        },
        "summary": {
            "requirements": len(specification),
            "phases": len(phases),
            "rest_proposals": sum(len(phase["steps"]) for phase in phases),
            "critical": sum(1 for row in issues if row.get("severity") == "critical"),
            "high": sum(1 for row in issues if row.get("severity") == "high"),
        },
        "technical_specification": specification,
        "implementation_phases": phases,
        "source_audit": {
            "version": audit.get("version"),
            "generated_at": audit.get("generated_at"),
            "status": audit.get("status"),
        },
    }


def blueprint_markdown(blueprint: dict[str, Any]) -> str:
    lines = [
        "# Техническое задание на доработку Bitrix24",
        "",
        f"Сформировано: {blueprint.get('generated_at', '')}",
        "",
        "**Режим:** READ-ONLY. Документ содержит предложения. AI-BIT не выполнял REST-запросы и не изменял портал.",
        "",
    ]
    for item in blueprint.get("technical_specification", []):
        lines.extend([
            f"## {item.get('number')}. {item.get('module')}",
            f"- Приоритет: {item.get('severity')}",
            f"- Объект: {item.get('object_ref') or 'требует уточнения'}",
            f"- Требование: {item.get('requirement')}",
            f"- Основание: {item.get('basis')}",
            f"- Критерий приёмки: {item.get('acceptance')}",
            f"- Источник: {item.get('source')}",
            "",
        ])
    return "\n".join(lines)
