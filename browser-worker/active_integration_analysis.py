from __future__ import annotations

import json
import re
from typing import Any

from onec_mcp_parser import decode_mcp_result

VERSION = "4.5.0"

STRUCTURE_CALLS = [
    {"id": "structure_catalog_counterparties", "name": "get_object_structure", "arguments": {"object_type": "Catalog", "object_name": "Контрагенты"}},
    {"id": "structure_catalog_partners", "name": "get_object_structure", "arguments": {"object_type": "Catalog", "object_name": "Партнеры"}},
    {"id": "structure_catalog_contacts", "name": "get_object_structure", "arguments": {"object_type": "Catalog", "object_name": "КонтактныеЛица"}},
    {"id": "structure_catalog_nomenclature", "name": "get_object_structure", "arguments": {"object_type": "Catalog", "object_name": "Номенклатура"}},
    {"id": "structure_document_customer_order", "name": "get_object_structure", "arguments": {"object_type": "Document", "object_name": "ЗаказКлиента"}},
    {"id": "structure_document_customer_invoice", "name": "get_object_structure", "arguments": {"object_type": "Document", "object_name": "СчетНаОплатуПокупателю"}},
]

ENTITY_CALLS = {
    "company_counterparty": ("structure_catalog_counterparties", "structure_catalog_partners"),
    "contact_person": ("structure_catalog_contacts",),
    "deal_order": ("structure_document_customer_order",),
    "product_nomenclature": ("structure_catalog_nomenclature",),
    "invoice_customer": ("structure_document_customer_invoice",),
}

FIELD_RULES = {
    "company_counterparty": [
        {"semantic": "name", "bitrix": ("TITLE",), "onec": ("Наименование", "НаименованиеПолное")},
        {"semantic": "tax_id", "bitrix": ("RQ_INN", "UF_CRM_INN", "UF_CRM_BIN"), "onec": ("ИНН", "БИН", "ИдентификационныйНомер")},
        {"semantic": "phone", "bitrix": ("PHONE",), "onec": ("Телефон", "НомерТелефона")},
        {"semantic": "email", "bitrix": ("EMAIL",), "onec": ("АдресЭлектроннойПочты", "Email", "ЭлектроннаяПочта")},
        {"semantic": "external_id", "bitrix": ("ORIGIN_ID", "UF_CRM_1C_ID", "XML_ID"), "onec": ("Ссылка", "Идентификатор", "ВнешнийИдентификатор", "GUID")},
    ],
    "contact_person": [
        {"semantic": "name", "bitrix": ("NAME", "LAST_NAME", "SECOND_NAME"), "onec": ("Наименование", "Фамилия", "Имя", "Отчество")},
        {"semantic": "phone", "bitrix": ("PHONE",), "onec": ("Телефон", "НомерТелефона")},
        {"semantic": "email", "bitrix": ("EMAIL",), "onec": ("АдресЭлектроннойПочты", "Email", "ЭлектроннаяПочта")},
        {"semantic": "company_link", "bitrix": ("COMPANY_ID",), "onec": ("Партнер", "Контрагент", "Владелец")},
        {"semantic": "external_id", "bitrix": ("ORIGIN_ID", "UF_CRM_1C_ID", "XML_ID"), "onec": ("Ссылка", "Идентификатор", "GUID")},
    ],
    "deal_order": [
        {"semantic": "number", "bitrix": ("ID", "UF_CRM_1C_NUMBER"), "onec": ("Номер",)},
        {"semantic": "date", "bitrix": ("DATE_CREATE", "BEGINDATE"), "onec": ("Дата",)},
        {"semantic": "company", "bitrix": ("COMPANY_ID",), "onec": ("Контрагент", "Партнер")},
        {"semantic": "amount", "bitrix": ("OPPORTUNITY",), "onec": ("СуммаДокумента", "Сумма")},
        {"semantic": "status", "bitrix": ("STAGE_ID",), "onec": ("Статус", "Состояние", "Проведен")},
        {"semantic": "external_id", "bitrix": ("ORIGIN_ID", "UF_CRM_1C_ID", "XML_ID"), "onec": ("Ссылка", "Идентификатор", "GUID")},
    ],
    "product_nomenclature": [
        {"semantic": "name", "bitrix": ("NAME",), "onec": ("Наименование", "НаименованиеПолное")},
        {"semantic": "sku", "bitrix": ("XML_ID", "PROPERTY_CML2_ARTICLE"), "onec": ("Артикул", "Код")},
        {"semantic": "price", "bitrix": ("PRICE",), "onec": ("Цена", "ВидЦены")},
        {"semantic": "unit", "bitrix": ("MEASURE",), "onec": ("ЕдиницаИзмерения", "ЕдиницаХранения")},
        {"semantic": "external_id", "bitrix": ("XML_ID", "ORIGIN_ID"), "onec": ("Ссылка", "Идентификатор", "GUID")},
    ],
    "invoice_customer": [
        {"semantic": "number", "bitrix": ("ACCOUNT_NUMBER", "ID"), "onec": ("Номер",)},
        {"semantic": "date", "bitrix": ("DATE_BILL", "DATE_INSERT"), "onec": ("Дата",)},
        {"semantic": "company", "bitrix": ("COMPANY_ID",), "onec": ("Контрагент", "Партнер")},
        {"semantic": "amount", "bitrix": ("PRICE", "OPPORTUNITY"), "onec": ("СуммаДокумента", "Сумма")},
        {"semantic": "status", "bitrix": ("STATUS_ID",), "onec": ("Статус", "Оплачен", "Проведен")},
        {"semantic": "external_id", "bitrix": ("ORIGIN_ID", "UF_CRM_1C_ID", "XML_ID"), "onec": ("Ссылка", "Идентификатор", "GUID")},
    ],
}

STRONG_MARKERS = ("bitrix", "битрикс", "bx24", "b24", "webhook", "вебхук")
MEDIUM_MARKERS = ("интеграц", "синхрон", "обмен", "odata")
WEAK_MARKERS = ("rest", "http", "crm")
CATEGORY_WEIGHT = {
    "metadata_exchange_plans": 35,
    "metadata_data_processors": 25,
    "metadata_common_modules": 20,
    "metadata_information_registers": 15,
    "metadata_documents": 8,
    "metadata_catalogs": 5,
}


def augment_active_calls(provider_id: str, allowed_tools: set[str], calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if provider_id != "mcp_1c" or "get_object_structure" not in allowed_tools:
        return calls
    existing = {str(row.get("id") or row.get("name") or "") for row in calls if isinstance(row, dict)}
    result = list(calls)
    for call in STRUCTURE_CALLS:
        if call["id"] not in existing:
            result.append(dict(call))
    return result


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def _normal(value: str) -> str:
    return re.sub(r"[^a-zа-яё0-9]", "", value.casefold())


def _call_payload(calls: dict[str, Any], call_id: str) -> Any:
    row = calls.get(call_id)
    if not isinstance(row, dict) or row.get("success") is not True:
        return None
    return decode_mcp_result(row.get("result"))


def _extract_fields(value: Any) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()

    def add(raw: Any) -> None:
        if not isinstance(raw, str):
            return
        value = raw.strip().strip("`*•-–—:;,. ")
        if not value or len(value) > 160:
            return
        key = _normal(value)
        if not key or key in seen or key in {"имя", "поле", "поля", "реквизиты", "тип", "объект"}:
            return
        seen.add(key)
        fields.append(value)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("name", "Имя", "field", "Поле", "attribute", "Реквизит", "Реквизиты"):
                candidate = node.get(key)
                if isinstance(candidate, list):
                    walk(candidate)
                else:
                    add(candidate)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            section = ""
            for line in node.splitlines():
                stripped = line.strip()
                heading = re.match(r"^#{1,6}\s*(.+)$", stripped)
                if heading:
                    section = heading.group(1).casefold()
                    continue
                if not any(token in section for token in ("реквиз", "пол", "атрибут", "таблич", "стандарт")):
                    continue
                match = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(?:\*\*)?([A-Za-zА-Яа-яЁё_][A-Za-zА-Яа-яЁё0-9_]*)", stripped)
                if match:
                    add(match.group(1))
                    continue
                table = re.match(r"^\|\s*([^|]+?)\s*\|", stripped)
                if table and not set(table.group(1).strip()) <= {"-", ":"}:
                    add(table.group(1))

    walk(value)
    return fields


def _structure_index(calls: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for call in STRUCTURE_CALLS:
        payload = _call_payload(calls, call["id"])
        object_name = str(call["arguments"]["object_name"])
        fields = _extract_fields(payload) if payload is not None else []
        result[_normal(object_name)] = {
            "call_id": call["id"],
            "object_type": call["arguments"]["object_type"],
            "object_name": object_name,
            "available": payload is not None,
            "decoded": bool(fields),
            "fields": fields,
            "field_count": len(fields),
        }
    return result


def _select_structure(mapping: dict[str, Any], index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    candidate = _normal(str(mapping.get("onec_candidate") or ""))
    if candidate and candidate in index:
        return index[candidate]
    for call_id in ENTITY_CALLS.get(str(mapping.get("id")), ()):
        for value in index.values():
            if value.get("call_id") == call_id and value.get("available"):
                return value
    return None


def _field_present(fields: list[str], aliases: tuple[str, ...]) -> tuple[bool, str | None]:
    normalized = {_normal(field): field for field in fields}
    for alias in aliases:
        target = _normal(alias)
        if target in normalized:
            return True, normalized[target]
    for alias in aliases:
        target = _normal(alias)
        if not target:
            continue
        for compact, original in normalized.items():
            if target in compact or compact in target:
                return True, original
    return False, None


def _bitrix_field_present(bitrix: dict[str, Any], aliases: tuple[str, ...]) -> tuple[bool, str | None]:
    haystack = _text(bitrix).casefold()
    for alias in aliases:
        if alias.casefold() in haystack:
            return True, alias
    return False, None


def _active_artifacts(raw_artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for row in raw_artifacts:
        name = str(row.get("name") or "")
        lowered = name.casefold()
        reasons: list[str] = []
        score = CATEGORY_WEIGHT.get(str(row.get("category") or ""), 0)
        strong = [token for token in STRONG_MARKERS if token in lowered]
        medium = [token for token in MEDIUM_MARKERS if token in lowered]
        weak = [token for token in WEAK_MARKERS if token in lowered]
        if strong:
            score += 70 + 10 * min(len(strong), 2)
            reasons.append("прямой маркер Bitrix24")
        if medium:
            score += 25 + 5 * min(len(medium), 2)
            reasons.append("маркер обмена или синхронизации")
        if weak:
            score += 5
            reasons.append("общий технический маркер")
        if score < 35:
            continue
        ranked.append({**row, "score": score, "confidence": min(1.0, score / 120), "reasons": reasons})
    ranked.sort(key=lambda item: (-int(item["score"]), str(item.get("name") or "").casefold()))
    return ranked[:50]


def enrich_verification_pipeline(base: dict[str, Any], bitrix: dict[str, Any], onec: dict[str, Any]) -> dict[str, Any]:
    calls = onec.get("calls") if isinstance(onec.get("calls"), dict) else {}
    structures = _structure_index(calls)
    mappings = base.get("entity_mappings") if isinstance(base.get("entity_mappings"), list) else []
    field_mappings: list[dict[str, Any]] = []
    verified_entities = 0

    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        structure = _select_structure(mapping, structures)
        structure_ready = bool(structure and structure.get("decoded"))
        if structure_ready:
            verified_entities += 1
        mapping["structure"] = structure or {"available": False, "decoded": False, "fields": [], "field_count": 0}
        mapping["structure_status"] = "confirmed" if structure_ready else "verification_required"
        for rule in FIELD_RULES.get(str(mapping.get("id")), []):
            onec_ok, onec_field = _field_present((structure or {}).get("fields", []), tuple(rule["onec"]))
            bitrix_ok, bitrix_field = _bitrix_field_present(bitrix, tuple(rule["bitrix"]))
            status = "confirmed_candidate" if onec_ok and bitrix_ok else "verification_required" if onec_ok or bitrix_ok else "insufficient_data"
            field_mappings.append({
                "entity_id": mapping.get("id"),
                "entity_label": mapping.get("label"),
                "semantic": rule["semantic"],
                "status": status,
                "bitrix_field": bitrix_field,
                "bitrix_candidates": list(rule["bitrix"]),
                "bitrix_evidence": bitrix_ok,
                "onec_field": onec_field,
                "onec_candidates": list(rule["onec"]),
                "onec_evidence": onec_ok,
                "finding": False,
            })

    raw_artifacts = base.get("integration_artifacts") if isinstance(base.get("integration_artifacts"), list) else []
    active_artifacts = _active_artifacts(raw_artifacts)
    confirmed_fields = sum(row["status"] == "confirmed_candidate" for row in field_mappings)
    pending_fields = sum(row["status"] == "verification_required" for row in field_mappings)

    for stage in base.get("stages", []):
        if not isinstance(stage, dict):
            continue
        if stage.get("id") == "detect_integration":
            stage["status"] = "confirmed" if active_artifacts else "no_evidence"
            stage["facts"] = {"raw_artifacts": len(raw_artifacts), "active_artifacts": len(active_artifacts)}
        elif stage.get("id") == "validate_mapping":
            stage["status"] = "confirmed" if verified_entities == len(mappings) and mappings else "in_progress"
            stage.setdefault("facts", {})["structures_confirmed"] = verified_entities
        elif stage.get("id") == "validate_fields":
            stage["status"] = "confirmed" if confirmed_fields and not pending_fields else "in_progress" if field_mappings else "waiting_for_structure"
            stage["facts"] = {"field_candidates": len(field_mappings), "confirmed_candidates": confirmed_fields, "verification_required": pending_fields}
        elif stage.get("id") == "validate_data":
            stage["status"] = "waiting_for_rules"
        elif stage.get("id") == "technical_conclusion":
            stage["status"] = "waiting_for_data_evidence"

    base["version"] = VERSION
    base["status"] = "field_mapping_in_progress" if verified_entities else "structure_verification_required"
    base["active_integration_artifacts"] = active_artifacts
    base["structures"] = list(structures.values())
    base["field_mappings"] = field_mappings
    base["analysis_summary"] = {
        "raw_artifacts": len(raw_artifacts),
        "active_artifacts": len(active_artifacts),
        "structures_requested": len(structures),
        "structures_decoded": sum(bool(row.get("decoded")) for row in structures.values()),
        "entities_with_structure": verified_entities,
        "field_candidates": len(field_mappings),
        "field_candidates_confirmed": confirmed_fields,
        "field_candidates_pending": pending_fields,
        "confirmed_findings": 0,
    }
    base["technical_conclusion"] = {
        "status": "draft_evidence_only",
        "facts": [
            f"Обнаружено {len(active_artifacts)} приоритетных технических точек интеграции из {len(raw_artifacts)} кандидатов.",
            f"Получена структура {verified_entities} из {len(mappings)} целевых сущностей.",
            f"Сформировано {len(field_mappings)} кандидатов сопоставления полей; подтверждено evidence с обеих сторон: {confirmed_fields}.",
        ],
        "findings": [],
        "limitations": [
            "Отсутствие поля не считается дефектом без полного описания структуры Bitrix24 и 1С.",
            "Проверка количества и содержимого данных будет выполнена только после настройки read-only правил выборки.",
        ],
    }
    return base
