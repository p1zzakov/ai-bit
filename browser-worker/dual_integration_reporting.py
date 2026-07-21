from __future__ import annotations

from collections import Counter
from typing import Any

VERSION = "4.7.0"

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_RU = {"critical": "Критический", "high": "Высокий", "medium": "Средний", "low": "Низкий"}
VERDICT_RU = {
    "architecturally_incorrect": "Архитектура интеграции содержит критические ошибки",
    "partially_verified": "Интеграция работает, но требует обязательной доработки и контрольной проверки данных",
    "requires_improvement": "Интеграция в целом работоспособна, но не полностью соответствует рекомендуемой архитектуре",
    "compliant": "Интеграция соответствует подтверждённым требованиям и может эксплуатироваться",
}
ADMISSION_RU = {
    "not_recommended": "Промышленная эксплуатация не рекомендуется до устранения критических замечаний",
    "not_recommended_until_data_validation": "Промышленный допуск нельзя подтвердить до сверки фактических данных",
    "allowed_with_restrictions": "Допустима эксплуатация с ограничениями и планом корректирующих мероприятий",
    "allowed": "Промышленная эксплуатация допустима",
}
AREA_RU = {
    "field_mapping": "Соответствие полей",
    "identity_strategy": "Идентификация объектов",
    "entity_model": "Модель сущностей",
    "architecture_control": "Архитектура и отказоустойчивость",
    "data_validation": "Проверка фактических данных",
}


def _human_problem(finding: dict[str, Any]) -> dict[str, Any]:
    severity = str(finding.get("severity") or "medium")
    title = str(finding.get("title") or "Требуется доработка интеграции")
    impact = str(finding.get("impact") or "Может снижать точность и устойчивость обмена данными.")
    recommendation = str(finding.get("recommendation") or "Уточнить реализацию и устранить подтверждённое отклонение.")
    return {
        "severity": severity,
        "severity_label": SEVERITY_RU.get(severity, severity),
        "title": title,
        "what_is_wrong": str(finding.get("fact") or "Обнаружено подтверждённое несоответствие."),
        "why_it_matters": impact,
        "what_to_do": recommendation,
        "result_after_fix": str(finding.get("acceptance") or "Результат подтверждён контрольным тестом."),
    }


def _positive_facts(pipeline: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    summary = pipeline.get("analysis_summary") if isinstance(pipeline.get("analysis_summary"), dict) else {}
    mappings = pipeline.get("entity_mappings") if isinstance(pipeline.get("entity_mappings"), list) else []
    fields = pipeline.get("field_mappings") if isinstance(pipeline.get("field_mappings"), list) else []
    controls = assessment.get("architecture_controls") if isinstance(assessment.get("architecture_controls"), list) else []
    rows = []
    decoded = int(summary.get("structures_decoded") or 0)
    if decoded:
        rows.append(f"Получены и разобраны структуры {decoded} целевых объектов 1С.")
    confirmed_entities = sum(x.get("structure_status") == "confirmed" for x in mappings)
    if confirmed_entities:
        rows.append(f"Подтверждена структура {confirmed_entities} ключевых сущностей обмена.")
    confirmed_fields = sum(x.get("status") == "confirmed_candidate" for x in fields)
    if confirmed_fields:
        rows.append(f"Найдено {confirmed_fields} подтверждённых кандидатов сопоставления полей Bitrix24 и 1С.")
    confirmed_controls = [str(x.get("title")) for x in controls if x.get("status") == "confirmed"]
    rows.extend(f"Подтверждено: {title}." for title in confirmed_controls[:4])
    return rows or ["Подключение к Bitrix24 и 1С работает; источники доступны для read-only аудита."]


def build_management_conclusion(pipeline: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    findings = assessment.get("confirmed_findings") if isinstance(assessment.get("confirmed_findings"), list) else []
    findings = sorted(findings, key=lambda x: SEVERITY_RANK.get(str(x.get("severity")), 9))
    severity = Counter(str(x.get("severity")) for x in findings)
    verdict = str(assessment.get("verdict") or "partially_verified")
    admission = str(assessment.get("industrial_admission") or "not_recommended_until_data_validation")
    data = assessment.get("data_validation") if isinstance(assessment.get("data_validation"), dict) else {}
    roadmap = []
    for index, row in enumerate((assessment.get("recommendations") or [])[:10], 1):
        roadmap.append({
            "step": index,
            "priority": str(row.get("severity") or "medium"),
            "title": str(row.get("task") or "Выполнить корректирующее мероприятие"),
            "why": str(row.get("business_impact") or row.get("basis") or "Требуется для повышения надёжности обмена."),
            "done_when": str(row.get("acceptance") or "Исправление подтверждено контрольной проверкой."),
        })
    return {
        "version": VERSION,
        "audience": "management",
        "title": "Заключение о качестве интеграции Bitrix24 и 1С",
        "quality_score": assessment.get("overall_score"),
        "verdict": verdict,
        "verdict_text": VERDICT_RU.get(verdict, verdict),
        "industrial_admission": admission,
        "industrial_admission_text": ADMISSION_RU.get(admission, admission),
        "executive_summary": (
            "Интеграционный контур технически доступен и частично подтверждён. "
            "При этом обнаруженные замечания затрагивают корректность сопоставления данных и устойчивость повторной синхронизации. "
            "До устранения критических замечаний и контрольной сверки записей нельзя достоверно подтвердить отсутствие дублей, потерь и ошибочной перезаписи данных."
            if findings or data.get("status") != "confirmed" else
            "Интеграция подтверждена по структуре, архитектурным контролям и фактическим данным; существенных отклонений не обнаружено."
        ),
        "what_works": _positive_facts(pipeline, assessment),
        "problems": [_human_problem(x) for x in findings],
        "severity_summary": {key: severity[key] for key in ("critical", "high", "medium", "low")},
        "data_validation_message": (
            "Фактическая полнота выгрузки пока не подтверждена: необходима сверка количества, внешних идентификаторов, дублей, расхождений и задержки обмена."
            if data.get("status") != "confirmed" else "Контрольные выборки данных выполнены и подтверждены."
        ),
        "roadmap": roadmap,
    }


def _technical_control(finding: dict[str, Any], index: int) -> dict[str, Any]:
    severity = str(finding.get("severity") or "medium")
    evidence = finding.get("evidence") if isinstance(finding.get("evidence"), dict) else {}
    return {
        "control_id": f"INT-{index:03d}",
        "status": "non_compliant",
        "severity": severity,
        "area": str(finding.get("area") or "integration"),
        "area_label": AREA_RU.get(str(finding.get("area") or ""), str(finding.get("area") or "integration")),
        "title": str(finding.get("title") or "Подтверждённое отклонение"),
        "observed_implementation": str(finding.get("fact") or "—"),
        "evidence": evidence,
        "violated_principle": (
            "Single stable identity / идемпотентная синхронизация" if finding.get("area") == "identity_strategy"
            else "Semantic field mapping / однозначное назначение данных" if finding.get("area") == "field_mapping"
            else "Наблюдаемая и проверяемая интеграционная архитектура"
        ),
        "failure_scenarios": [str(finding.get("impact") or "Возможны ошибки синхронизации и нарушение целостности данных.")],
        "required_implementation": str(finding.get("recommendation") or "Исправить реализацию согласно назначению данных."),
        "acceptance_test": str(finding.get("acceptance") or "Исправление подтверждено повторяемым read-only тестом."),
        "owner": "Интегратор / разработчик 1С",
    }


def build_technical_conclusion(pipeline: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    findings = assessment.get("confirmed_findings") if isinstance(assessment.get("confirmed_findings"), list) else []
    findings = sorted(findings, key=lambda x: SEVERITY_RANK.get(str(x.get("severity")), 9))
    controls = assessment.get("architecture_controls") if isinstance(assessment.get("architecture_controls"), list) else []
    unconfirmed = [{
        "control_id": f"ARCH-{index:03d}",
        "title": str(row.get("title") or row.get("id")),
        "status": "verification_required",
        "reason": str(row.get("note") or "Механизм не подтверждён evidence."),
        "required_evidence": "Описание реализации, объект/модуль 1С, REST-метод Bitrix24, журнал выполнения и контрольный сценарий.",
    } for index, row in enumerate((x for x in controls if x.get("status") != "confirmed"), 1)]
    field_map = pipeline.get("field_mappings") if isinstance(pipeline.get("field_mappings"), list) else []
    mapping_matrix = [{
        "entity": row.get("entity_label") or row.get("entity_id"),
        "semantic": row.get("semantic"),
        "bitrix_field": row.get("bitrix_field"),
        "onec_field": row.get("onec_field"),
        "status": row.get("status"),
        "bitrix_evidence": bool(row.get("bitrix_evidence")),
        "onec_evidence": bool(row.get("onec_evidence")),
    } for row in field_map]
    return {
        "version": VERSION,
        "audience": "integrator_and_1c_developer",
        "title": "Технический акт проверки интеграции Bitrix24 ↔ 1С",
        "scope": ["модель сущностей", "семантика полей", "внешние ключи", "идемпотентность", "очереди и retry", "журналирование", "контроль фактических данных"],
        "method": "Read-only evidence → структура объектов → семантический mapping → best-practice controls → критерии приёмки",
        "confirmed_nonconformities": [_technical_control(x, i) for i, x in enumerate(findings, 1)],
        "controls_requiring_verification": unconfirmed,
        "field_mapping_matrix": mapping_matrix,
        "implementation_plan": assessment.get("recommendations") or [],
        "data_validation_specification": {
            "required": True,
            "checks": (assessment.get("data_validation") or {}).get("required_checks") or [],
            "minimum_sample": "Не менее 100 объектов каждой ключевой сущности либо 100% при объёме менее 100 записей.",
            "required_metrics": ["полнота выгрузки", "уникальность внешнего ID", "доля расхождений", "максимальная задержка", "число ошибок/retry", "повторная отправка без дубля"],
        },
        "release_gate": {
            "decision": assessment.get("industrial_admission"),
            "blocking_conditions": [
                "Все critical/high несоответствия закрыты и подтверждены acceptance-тестами.",
                "Для каждой сущности назначена мастер-система и стабильный внешний идентификатор.",
                "Контрольная выборка не выявляет дублей, потерь и семантических расхождений.",
                "Ошибки обмена журналируются, retry воспроизводим и не создаёт дубли.",
            ],
        },
    }


def enrich_with_dual_reports(pipeline: dict[str, Any]) -> dict[str, Any]:
    assessment = pipeline.get("best_practice_assessment") if isinstance(pipeline.get("best_practice_assessment"), dict) else {}
    pipeline["management_conclusion"] = build_management_conclusion(pipeline, assessment)
    pipeline["technical_conclusion_v2"] = build_technical_conclusion(pipeline, assessment)
    pipeline["version"] = VERSION
    return pipeline
