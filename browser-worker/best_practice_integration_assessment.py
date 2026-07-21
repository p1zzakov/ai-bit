from __future__ import annotations

from collections import Counter
from typing import Any

VERSION = "4.6.0"

DIMENSION_WEIGHTS = {
    "entity_model": 20,
    "field_semantics": 25,
    "identity_strategy": 20,
    "reliability": 15,
    "observability": 10,
    "data_validation": 10,
}

SEMANTIC_LABELS = {
    "name": "Наименование",
    "tax_id": "БИН/ИИН",
    "phone": "Телефон",
    "email": "E-mail",
    "external_id": "Внешний идентификатор",
    "number": "Номер документа",
    "date": "Дата документа",
    "company": "Контрагент/компания",
    "amount": "Сумма",
    "status": "Статус",
    "sku": "Артикул",
    "price": "Цена",
    "unit": "Единица измерения",
    "company_link": "Связь с компанией",
}

# Пары, которые существуют технически, но противоречат смыслу данных.
DANGEROUS_PAIR_RULES = (
    {
        "entity": "deal_order",
        "semantic": "date",
        "bitrix": ("DATE_CREATE",),
        "onec": ("ЖелаемаяДатаОтгрузки", "ДатаОтгрузки"),
        "severity": "high",
        "title": "Дата создания сделки сопоставлена с датой отгрузки",
        "impact": "Искажается хронология заказа, аналитика сроков и контроль SLA.",
        "fix": "Разделить дату создания, дату заказа и желаемую дату отгрузки на самостоятельные поля.",
        "acceptance": "Для контрольной выборки даты в Bitrix24 и 1С совпадают по назначению, а не только по типу.",
    },
    {
        "entity": "deal_order",
        "semantic": "external_id",
        "bitrix": ("ORIGIN_ID", "XML_ID", "UF_CRM_1C_ID"),
        "onec": ("ИдентификаторПлатежа", "PaymentId"),
        "severity": "critical",
        "title": "Внешний ключ сделки сопоставлен с идентификатором платежа",
        "impact": "Возможны дубли заказов, потеря связи при повторной выгрузке и ошибочное обновление чужого документа.",
        "fix": "Использовать неизменяемую ссылку/GUID заказа 1С как отдельный внешний ключ сделки.",
        "acceptance": "Повторная выгрузка одного заказа обновляет одну и ту же сделку и не создаёт дубль.",
    },
    {
        "entity": "deal_order",
        "semantic": "number",
        "bitrix": ("ID",),
        "onec": ("НомерПоДаннымКлиента",),
        "severity": "high",
        "title": "Внутренний ID сделки используется как номер заказа клиента",
        "impact": "Номер не отражает номер документа 1С и может быть непереносим между порталами/контурами.",
        "fix": "Хранить номер заказа 1С в отдельном поле, не подменяя его внутренним ID Bitrix24.",
        "acceptance": "В карточке сделки отдельно доступны внутренний ID Bitrix24, номер заказа 1С и внешний GUID.",
    },
)

ARCHITECTURE_CONTROLS = (
    ("master_system", "Определена мастер-система по каждой сущности", ("master", "мастер", "источник истины", "source of truth")),
    ("stable_identity", "Используется устойчивый внешний идентификатор", ("origin_id", "xml_id", "guid", "внешнийидентификатор")),
    ("idempotency", "Повторная отправка не создаёт дубликаты", ("идемпот", "idempot", "дублик", "повторн")),
    ("retry_queue", "Есть очередь и повторные попытки", ("очеред", "retry", "повторная попыт", "повторные попыт")),
    ("error_log", "Есть журнал ошибок обмена", ("журнал", "лог", "error", "ошиб")),
    ("incremental_exchange", "Используется инкрементальный обмен", ("инкремент", "изменен", "дельт", "delta", "регистрация изменений")),
    ("conflict_policy", "Определена политика разрешения конфликтов", ("конфликт", "приоритет данных", "разрешение конфликт")),
    ("monitoring", "Настроен мониторинг задержек и ошибок", ("монитор", "метрик", "alert", "уведомлен")),
)


def _lower(value: Any) -> str:
    return str(value or "").casefold()


def _contains_any(value: Any, tokens: tuple[str, ...]) -> bool:
    text = _lower(value)
    return any(token.casefold() in text for token in tokens)


def _finding(
    *,
    code: str,
    severity: str,
    area: str,
    title: str,
    fact: str,
    impact: str,
    fix: str,
    acceptance: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "area": area,
        "title": title,
        "fact": fact,
        "impact": impact,
        "recommendation": fix,
        "acceptance": acceptance,
        "evidence": evidence,
        "status": "confirmed",
    }


def _semantic_findings(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for row in fields:
        entity = str(row.get("entity_id") or "")
        semantic = str(row.get("semantic") or "")
        bx = str(row.get("bitrix_field") or "")
        oc = str(row.get("onec_field") or "")
        if not bx or not oc:
            continue
        for rule in DANGEROUS_PAIR_RULES:
            if entity != rule["entity"] or semantic != rule["semantic"]:
                continue
            if not _contains_any(bx, rule["bitrix"]) or not _contains_any(oc, rule["onec"]):
                continue
            findings.append(_finding(
                code=f"semantic.{entity}.{semantic}",
                severity=str(rule["severity"]),
                area="field_mapping",
                title=str(rule["title"]),
                fact=f"{bx} ↔ {oc}",
                impact=str(rule["impact"]),
                fix=str(rule["fix"]),
                acceptance=str(rule["acceptance"]),
                evidence={"entity": entity, "semantic": semantic, "bitrix_field": bx, "onec_field": oc},
            ))
    return findings


def _identity_findings(fields: list[dict[str, Any]], mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    confirmed_entities = {
        str(row.get("id"))
        for row in mappings
        if row.get("structure_status") == "confirmed" or row.get("status") == "confirmed_candidate"
    }
    external_rows = [row for row in fields if row.get("semantic") == "external_id"]
    by_entity = {str(row.get("entity_id")): row for row in external_rows}
    for entity in confirmed_entities:
        row = by_entity.get(entity)
        if not row:
            continue
        if row.get("bitrix_evidence") and row.get("onec_evidence"):
            continue
        findings.append(_finding(
            code=f"identity.{entity}.not_confirmed",
            severity="high",
            area="identity_strategy",
            title="Не подтверждён устойчивый внешний ключ",
            fact=f"Для {row.get('entity_label') or entity} внешний идентификатор не подтверждён с обеих сторон.",
            impact="Повторная синхронизация может создавать дубли или обновлять неверные записи.",
            fix="Зафиксировать отдельный неизменяемый GUID/ссылку 1С и хранить его в выделенном поле Bitrix24.",
            acceptance="Создание, повторная отправка и обновление одной записи сохраняют единственную связанную пару объектов.",
            evidence=row,
        ))
    return findings


def _duplicate_identity_findings(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for entity in sorted({str(row.get("entity_id")) for row in fields}):
        rows = [row for row in fields if str(row.get("entity_id")) == entity]
        by_bx: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            bx = str(row.get("bitrix_field") or "")
            if bx:
                by_bx.setdefault(bx, []).append(row)
        for bx, duplicates in by_bx.items():
            semantics = {str(row.get("semantic")) for row in duplicates}
            if "external_id" in semantics and len(semantics) > 1:
                findings.append(_finding(
                    code=f"identity.{entity}.field_reused.{bx}",
                    severity="high",
                    area="identity_strategy",
                    title="Одно поле Bitrix24 используется для разных смыслов",
                    fact=f"Поле {bx} назначено для: {', '.join(sorted(semantics))}.",
                    impact="Идентификатор может быть перезаписан артикулом, номером или другим бизнес-значением.",
                    fix="Разнести внешний GUID, артикул, номер документа и иные значения по отдельным полям.",
                    acceptance="Каждое интеграционное поле имеет одно назначение, тип и владельца данных.",
                    evidence={"entity": entity, "bitrix_field": bx, "rows": duplicates},
                ))
    return findings


def _architecture_controls(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_text = " ".join(
        str(value)
        for value in (
            pipeline.get("active_integration_artifacts"),
            pipeline.get("integration_artifacts"),
            pipeline.get("field_mappings"),
            pipeline.get("technical_conclusion"),
        )
    )
    controls = []
    for control_id, title, tokens in ARCHITECTURE_CONTROLS:
        confirmed = _contains_any(evidence_text, tokens)
        controls.append({
            "id": control_id,
            "title": title,
            "status": "confirmed" if confirmed else "not_confirmed",
            "finding": False,
            "note": "Отсутствие evidence не доказывает отсутствие механизма; требуется проверка реализации." if not confirmed else "Механизм обнаружен в evidence.",
        })
    return controls


def _dimension_scores(
    pipeline: dict[str, Any],
    controls: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    data_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mappings = pipeline.get("entity_mappings") if isinstance(pipeline.get("entity_mappings"), list) else []
    fields = pipeline.get("field_mappings") if isinstance(pipeline.get("field_mappings"), list) else []
    confirmed_mappings = sum(row.get("structure_status") == "confirmed" for row in mappings)
    confirmed_fields = sum(row.get("status") == "confirmed_candidate" for row in fields)
    total_fields = len(fields)
    control_confirmed = sum(row.get("status") == "confirmed" for row in controls)
    critical = sum(row.get("severity") == "critical" for row in findings)
    high = sum(row.get("severity") == "high" for row in findings)
    data_confirmed = sum(row.get("status") == "confirmed" for row in data_checks)

    values = {
        "entity_model": round(100 * confirmed_mappings / max(1, len(mappings))),
        "field_semantics": max(0, round(100 * confirmed_fields / max(1, total_fields)) - critical * 30 - high * 12),
        "identity_strategy": max(0, 100 - sum(row.get("area") == "identity_strategy" for row in findings) * 30),
        "reliability": round(100 * sum(row.get("id") in {"idempotency", "retry_queue", "incremental_exchange", "conflict_policy"} and row.get("status") == "confirmed" for row in controls) / 4),
        "observability": round(100 * sum(row.get("id") in {"error_log", "monitoring"} and row.get("status") == "confirmed" for row in controls) / 2),
        "data_validation": round(100 * data_confirmed / max(1, len(data_checks))) if data_checks else 0,
    }
    result = []
    for dimension, weight in DIMENSION_WEIGHTS.items():
        score = int(values.get(dimension, 0))
        result.append({
            "id": dimension,
            "score": score,
            "weight": weight,
            "weighted_score": round(score * weight / 100, 1),
            "status": "good" if score >= 80 else "attention" if score >= 50 else "critical" if score < 30 else "weak",
        })
    return result


def _recommendations(findings: list[dict[str, Any]], controls: list[dict[str, Any]], data_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recommendations = []
    for index, finding in enumerate(sorted(findings, key=lambda row: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(row.get("severity")), 4)), 1):
        recommendations.append({
            "priority": index,
            "severity": finding.get("severity"),
            "area": finding.get("area"),
            "task": finding.get("recommendation"),
            "basis": finding.get("fact"),
            "business_impact": finding.get("impact"),
            "acceptance": finding.get("acceptance"),
            "execution": "proposal_only",
        })
    next_priority = len(recommendations) + 1
    for control in controls:
        if control.get("status") == "confirmed":
            continue
        recommendations.append({
            "priority": next_priority,
            "severity": "medium",
            "area": "architecture_control",
            "task": f"Подтвердить и документировать: {control.get('title')}",
            "basis": "Механизм не подтверждён собранным evidence.",
            "business_impact": "Без проверки невозможно объективно оценить устойчивость и сопровождаемость обмена.",
            "acceptance": "Предоставлена схема реализации и успешно выполнен read-only контрольный тест.",
            "execution": "proposal_only",
        })
        next_priority += 1
    if not data_checks:
        recommendations.append({
            "priority": next_priority,
            "severity": "high",
            "area": "data_validation",
            "task": "Настроить read-only контрольные выборки и сверку фактических данных",
            "basis": "Количество, дубли, расхождения и задержка синхронизации ещё не проверены.",
            "business_impact": "Корректная структура не гарантирует полноту и актуальность фактической выгрузки.",
            "acceptance": "Сверены контрольные выборки по всем ключевым сущностям, рассчитаны расхождения и задержка обмена.",
            "execution": "proposal_only",
        })
    return recommendations


def build_best_practice_assessment(
    pipeline: dict[str, Any],
    *,
    data_checks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data_checks = data_checks or []
    fields = pipeline.get("field_mappings") if isinstance(pipeline.get("field_mappings"), list) else []
    mappings = pipeline.get("entity_mappings") if isinstance(pipeline.get("entity_mappings"), list) else []

    findings = [
        *_semantic_findings(fields),
        *_identity_findings(fields, mappings),
        *_duplicate_identity_findings(fields),
    ]
    # Убираем дубли правил, оставляя первое и наиболее конкретное доказательство.
    unique: dict[str, dict[str, Any]] = {}
    for finding in findings:
        unique.setdefault(str(finding.get("code")), finding)
    findings = list(unique.values())

    controls = _architecture_controls(pipeline)
    dimensions = _dimension_scores(pipeline, controls, findings, data_checks)
    overall_score = round(sum(float(row["weighted_score"]) for row in dimensions), 1)
    severity = Counter(str(row.get("severity")) for row in findings)
    data_validated = bool(data_checks) and all(row.get("status") == "confirmed" for row in data_checks)

    if severity["critical"]:
        verdict = "architecturally_incorrect"
        admission = "not_recommended"
    elif severity["high"] or not data_validated:
        verdict = "partially_verified"
        admission = "allowed_with_restrictions" if data_checks else "not_recommended_until_data_validation"
    elif overall_score >= 80:
        verdict = "compliant"
        admission = "allowed"
    else:
        verdict = "requires_improvement"
        admission = "allowed_with_restrictions"

    recommendations = _recommendations(findings, controls, data_checks)
    return {
        "version": VERSION,
        "methodology": "evidence-based best-practice assessment",
        "mode": "read_only",
        "verdict": verdict,
        "industrial_admission": admission,
        "overall_score": overall_score,
        "dimensions": dimensions,
        "severity_summary": {
            "critical": severity["critical"],
            "high": severity["high"],
            "medium": severity["medium"],
            "low": severity["low"],
        },
        "confirmed_findings": findings,
        "architecture_controls": controls,
        "recommendations": recommendations,
        "data_validation": {
            "status": "confirmed" if data_validated else "not_configured" if not data_checks else "partial",
            "checks_total": len(data_checks),
            "checks_confirmed": sum(row.get("status") == "confirmed" for row in data_checks),
            "required_checks": [
                "Сверка количества объектов",
                "Дубликаты внешних идентификаторов",
                "Объекты только в одной системе",
                "Расхождения ключевых значений",
                "Дата и задержка последней синхронизации",
                "Ошибки и повторные попытки",
                "Выборочная сверка записей",
            ],
        },
        "limitations": [
            "Оценка не считает отсутствие evidence доказанным дефектом.",
            "Фактическая корректность выгрузки подтверждается только контрольными read-only выборками данных.",
            "Все рекомендации являются предложениями; автоматические изменения в Bitrix24 и 1С запрещены.",
        ],
    }
