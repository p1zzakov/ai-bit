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

DANGEROUS_PAIR_RULES = (
    {
        "entity": "deal_order", "semantic": "date",
        "bitrix": ("DATE_CREATE",), "onec": ("ЖелаемаяДатаОтгрузки", "ДатаОтгрузки"),
        "severity": "high", "title": "Дата создания сделки сопоставлена с датой отгрузки",
        "impact": "Искажается хронология заказа, аналитика сроков и контроль SLA.",
        "fix": "Разделить дату создания, дату заказа и желаемую дату отгрузки на самостоятельные поля.",
        "acceptance": "Для контрольной выборки даты в Bitrix24 и 1С совпадают по назначению, а не только по типу.",
    },
    {
        "entity": "deal_order", "semantic": "external_id",
        "bitrix": ("ORIGIN_ID", "XML_ID", "UF_CRM_1C_ID"), "onec": ("ИдентификаторПлатежа", "PaymentId"),
        "severity": "critical", "title": "Внешний ключ сделки сопоставлен с идентификатором платежа",
        "impact": "Возможны дубли заказов, потеря связи при повторной выгрузке и обновление неверного документа.",
        "fix": "Использовать неизменяемую ссылку/GUID заказа 1С как отдельный внешний ключ сделки.",
        "acceptance": "Повторная выгрузка одного заказа обновляет одну и ту же сделку и не создаёт дубль.",
    },
    {
        "entity": "deal_order", "semantic": "number",
        "bitrix": ("ID",), "onec": ("НомерПоДаннымКлиента",),
        "severity": "high", "title": "Внутренний ID сделки используется как номер заказа клиента",
        "impact": "Номер не отражает номер документа 1С и непереносим между порталами/контурами.",
        "fix": "Хранить номер заказа 1С в отдельном поле, не подменяя его внутренним ID Bitrix24.",
        "acceptance": "Отдельно доступны ID Bitrix24, номер заказа 1С и внешний GUID.",
    },
)

ARCHITECTURE_CONTROLS = (
    ("master_system", "Определена мастер-система по каждой сущности", ("master", "мастер", "источник истины", "source of truth")),
    ("stable_identity", "Используется устойчивый внешний идентификатор", ("origin_id", "xml_id", "guid", "внешнийидентификатор")),
    ("idempotency", "Повторная отправка не создаёт дубликаты", ("идемпот", "idempot", "дублик", "повторн")),
    ("retry_queue", "Есть очередь и повторные попытки", ("очеред", "retry", "повторная попыт", "повторные попыт")),
    ("error_log", "Есть журнал ошибок обмена", ("журнал", "лог", "error", "ошиб")),
    ("incremental_exchange", "Используется инкрементальный обмен", ("инкремент", "дельт", "delta", "регистрация изменений")),
    ("conflict_policy", "Определена политика разрешения конфликтов", ("конфликт", "приоритет данных", "разрешение конфликт")),
    ("monitoring", "Настроен мониторинг задержек и ошибок", ("монитор", "метрик", "alert", "уведомлен")),
)


def _contains_any(value: Any, tokens: tuple[str, ...]) -> bool:
    text = str(value or "").casefold()
    return any(token.casefold() in text for token in tokens)


def _finding(code: str, severity: str, area: str, title: str, fact: str, impact: str, fix: str, acceptance: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"code": code, "severity": severity, "area": area, "title": title, "fact": fact,
            "impact": impact, "recommendation": fix, "acceptance": acceptance,
            "evidence": evidence, "status": "confirmed"}


def _semantic_findings(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in fields:
        entity, semantic = str(row.get("entity_id") or ""), str(row.get("semantic") or "")
        bx, oc = str(row.get("bitrix_field") or ""), str(row.get("onec_field") or "")
        if not bx or not oc:
            continue
        for rule in DANGEROUS_PAIR_RULES:
            if entity == rule["entity"] and semantic == rule["semantic"] and _contains_any(bx, rule["bitrix"]) and _contains_any(oc, rule["onec"]):
                result.append(_finding(f"semantic.{entity}.{semantic}", str(rule["severity"]), "field_mapping",
                    str(rule["title"]), f"{bx} ↔ {oc}", str(rule["impact"]), str(rule["fix"]),
                    str(rule["acceptance"]), {"entity": entity, "semantic": semantic, "bitrix_field": bx, "onec_field": oc}))
    return result


def _identity_findings(fields: list[dict[str, Any]], mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    confirmed = {str(x.get("id")) for x in mappings if x.get("structure_status") == "confirmed" or x.get("status") == "confirmed_candidate"}
    external = {str(x.get("entity_id")): x for x in fields if x.get("semantic") == "external_id"}
    for entity in confirmed:
        row = external.get(entity)
        if row and not (row.get("bitrix_evidence") and row.get("onec_evidence")):
            result.append(_finding(f"identity.{entity}.not_confirmed", "high", "identity_strategy",
                "Не подтверждён устойчивый внешний ключ", f"Для {row.get('entity_label') or entity} внешний идентификатор не подтверждён с обеих сторон.",
                "Повторная синхронизация может создавать дубли или обновлять неверные записи.",
                "Зафиксировать отдельный неизменяемый GUID/ссылку 1С и хранить его в выделенном поле Bitrix24.",
                "Создание, повторная отправка и обновление сохраняют единственную связанную пару объектов.", row))
    return result


def _field_reuse_findings(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    entities = {str(x.get("entity_id")) for x in fields}
    for entity in entities:
        by_bx: dict[str, list[dict[str, Any]]] = {}
        for row in fields:
            if str(row.get("entity_id")) == entity and row.get("bitrix_field"):
                by_bx.setdefault(str(row["bitrix_field"]), []).append(row)
        for bx, rows in by_bx.items():
            semantics = {str(x.get("semantic")) for x in rows}
            if "external_id" in semantics and len(semantics) > 1:
                result.append(_finding(f"identity.{entity}.field_reused.{bx}", "high", "identity_strategy",
                    "Одно поле Bitrix24 используется для разных смыслов", f"Поле {bx} назначено для: {', '.join(sorted(semantics))}.",
                    "Идентификатор может быть перезаписан артикулом, номером или иным бизнес-значением.",
                    "Разнести внешний GUID, артикул, номер документа и другие значения по отдельным полям.",
                    "Каждое интеграционное поле имеет одно назначение, тип и владельца данных.",
                    {"entity": entity, "bitrix_field": bx, "rows": rows}))
    return result


def _architecture_controls(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = " ".join(str(pipeline.get(key)) for key in ("active_integration_artifacts", "integration_artifacts", "field_mappings", "technical_conclusion"))
    return [{"id": cid, "title": title, "status": "confirmed" if _contains_any(evidence, tokens) else "not_confirmed",
             "finding": False, "note": "Механизм обнаружен в evidence." if _contains_any(evidence, tokens) else "Отсутствие evidence не доказывает отсутствие механизма; требуется проверка реализации."}
            for cid, title, tokens in ARCHITECTURE_CONTROLS]


def _dimensions(pipeline: dict[str, Any], controls: list[dict[str, Any]], findings: list[dict[str, Any]], data_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mappings = pipeline.get("entity_mappings") if isinstance(pipeline.get("entity_mappings"), list) else []
    fields = pipeline.get("field_mappings") if isinstance(pipeline.get("field_mappings"), list) else []
    critical = sum(x.get("severity") == "critical" for x in findings)
    high = sum(x.get("severity") == "high" for x in findings)
    values = {
        "entity_model": round(100 * sum(x.get("structure_status") == "confirmed" for x in mappings) / max(1, len(mappings))),
        "field_semantics": max(0, round(100 * sum(x.get("status") == "confirmed_candidate" for x in fields) / max(1, len(fields))) - critical * 30 - high * 12),
        "identity_strategy": max(0, 100 - sum(x.get("area") == "identity_strategy" for x in findings) * 30),
        "reliability": round(100 * sum(x.get("id") in {"idempotency", "retry_queue", "incremental_exchange", "conflict_policy"} and x.get("status") == "confirmed" for x in controls) / 4),
        "observability": round(100 * sum(x.get("id") in {"error_log", "monitoring"} and x.get("status") == "confirmed" for x in controls) / 2),
        "data_validation": round(100 * sum(x.get("status") == "confirmed" for x in data_checks) / max(1, len(data_checks))) if data_checks else 0,
    }
    return [{"id": key, "score": int(values[key]), "weight": weight, "weighted_score": round(values[key] * weight / 100, 1),
             "status": "good" if values[key] >= 80 else "attention" if values[key] >= 50 else "critical" if values[key] < 30 else "weak"}
            for key, weight in DIMENSION_WEIGHTS.items()]


def _recommendations(findings: list[dict[str, Any]], controls: list[dict[str, Any]], data_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    rows = []
    for idx, finding in enumerate(sorted(findings, key=lambda x: order.get(str(x.get("severity")), 4)), 1):
        rows.append({"priority": idx, "severity": finding.get("severity"), "area": finding.get("area"),
                     "task": finding.get("recommendation"), "basis": finding.get("fact"),
                     "business_impact": finding.get("impact"), "acceptance": finding.get("acceptance"), "execution": "proposal_only"})
    priority = len(rows) + 1
    for control in controls:
        if control.get("status") != "confirmed":
            rows.append({"priority": priority, "severity": "medium", "area": "architecture_control",
                         "task": f"Подтвердить и документировать: {control.get('title')}",
                         "basis": "Механизм не подтверждён собранным evidence.",
                         "business_impact": "Без проверки невозможно объективно оценить устойчивость обмена.",
                         "acceptance": "Предоставлена схема реализации и выполнен read-only контрольный тест.", "execution": "proposal_only"})
            priority += 1
    if not data_checks:
        rows.append({"priority": priority, "severity": "high", "area": "data_validation",
                     "task": "Настроить read-only контрольные выборки и сверку фактических данных",
                     "basis": "Количество, дубли, расхождения и задержка синхронизации ещё не проверены.",
                     "business_impact": "Корректная структура не гарантирует полноту и актуальность выгрузки.",
                     "acceptance": "Сверены выборки по ключевым сущностям, рассчитаны расхождения и задержка обмена.", "execution": "proposal_only"})
    return rows


def build_best_practice_assessment(pipeline: dict[str, Any], *, data_checks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data_checks = data_checks or []
    fields = pipeline.get("field_mappings") if isinstance(pipeline.get("field_mappings"), list) else []
    mappings = pipeline.get("entity_mappings") if isinstance(pipeline.get("entity_mappings"), list) else []
    raw = [*_semantic_findings(fields), *_identity_findings(fields, mappings), *_field_reuse_findings(fields)]
    findings = list({str(x.get("code")): x for x in raw}.values())
    controls = _architecture_controls(pipeline)
    dimensions = _dimensions(pipeline, controls, findings, data_checks)
    score = round(sum(float(x["weighted_score"]) for x in dimensions), 1)
    severity = Counter(str(x.get("severity")) for x in findings)
    data_validated = bool(data_checks) and all(x.get("status") == "confirmed" for x in data_checks)
    if severity["critical"]:
        verdict, admission = "architecturally_incorrect", "not_recommended"
    elif severity["high"] or not data_validated:
        verdict = "partially_verified"
        admission = "allowed_with_restrictions" if data_checks else "not_recommended_until_data_validation"
    elif score >= 80:
        verdict, admission = "compliant", "allowed"
    else:
        verdict, admission = "requires_improvement", "allowed_with_restrictions"
    return {
        "version": VERSION, "methodology": "evidence-based best-practice assessment", "mode": "read_only",
        "verdict": verdict, "industrial_admission": admission, "overall_score": score,
        "dimensions": dimensions,
        "severity_summary": {key: severity[key] for key in ("critical", "high", "medium", "low")},
        "confirmed_findings": findings, "architecture_controls": controls,
        "recommendations": _recommendations(findings, controls, data_checks),
        "data_validation": {"status": "confirmed" if data_validated else "not_configured" if not data_checks else "partial",
            "checks_total": len(data_checks), "checks_confirmed": sum(x.get("status") == "confirmed" for x in data_checks),
            "required_checks": ["Сверка количества объектов", "Дубликаты внешних идентификаторов", "Объекты только в одной системе", "Расхождения ключевых значений", "Дата и задержка последней синхронизации", "Ошибки и повторные попытки", "Выборочная сверка записей"]},
        "limitations": ["Отсутствие evidence не считается доказанным дефектом.", "Корректность выгрузки подтверждается контрольными read-only выборками данных.", "Автоматические изменения в Bitrix24 и 1С запрещены."],
    }
