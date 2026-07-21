from __future__ import annotations

import json
import re
from typing import Any

from onec_mcp_parser import decode_mcp_result

VERSION = "4.4.0"

DISCOVERY_CALLS = [
    {"id": "metadata_catalogs", "name": "get_metadata_tree", "arguments": {"filter": "Справочники"}},
    {"id": "metadata_documents", "name": "get_metadata_tree", "arguments": {"filter": "Документы"}},
    {"id": "metadata_exchange_plans", "name": "get_metadata_tree", "arguments": {"filter": "ПланыОбмена"}},
    {"id": "metadata_information_registers", "name": "get_metadata_tree", "arguments": {"filter": "РегистрыСведений"}},
    {"id": "metadata_data_processors", "name": "get_metadata_tree", "arguments": {"filter": "Обработки"}},
    {"id": "metadata_common_modules", "name": "get_metadata_tree", "arguments": {"filter": "ОбщиеМодули"}},
]

ENTITY_RULES = [
    {
        "id": "company_counterparty",
        "label": "Компания ↔ Контрагент",
        "bitrix": "crm.company",
        "onec_type": "Catalog",
        "categories": ("metadata_catalogs",),
        "tokens": ("контрагент", "партнер", "партнёр", "клиент", "организац"),
        "preferred": ("Контрагенты", "Партнеры"),
    },
    {
        "id": "contact_person",
        "label": "Контакт ↔ Контактное лицо",
        "bitrix": "crm.contact",
        "onec_type": "Catalog",
        "categories": ("metadata_catalogs",),
        "tokens": ("контактн", "контактные лица", "физическ"),
        "preferred": ("КонтактныеЛица", "КонтактныеЛицаКонтрагентов"),
    },
    {
        "id": "deal_order",
        "label": "Сделка ↔ Заказ клиента",
        "bitrix": "crm.deal",
        "onec_type": "Document",
        "categories": ("metadata_documents",),
        "tokens": ("заказ клиент", "заказ покупател", "заказ"),
        "preferred": ("ЗаказКлиента", "ЗаказПокупателя"),
    },
    {
        "id": "product_nomenclature",
        "label": "Товар ↔ Номенклатура",
        "bitrix": "crm.product",
        "onec_type": "Catalog",
        "categories": ("metadata_catalogs",),
        "tokens": ("номенклатур", "товар", "продукц"),
        "preferred": ("Номенклатура", "Товары"),
    },
    {
        "id": "invoice_customer",
        "label": "Счёт ↔ Счёт покупателю",
        "bitrix": "crm.invoice",
        "onec_type": "Document",
        "categories": ("metadata_documents",),
        "tokens": ("счет на оплат", "счёт на оплат", "счет покупател", "счёт покупател"),
        "preferred": ("СчетНаОплатуПокупателю", "СчетПокупателю"),
    },
]

INTEGRATION_TOKENS = (
    "bitrix", "битрикс", "crm", "rest", "webhook", "вебхук", "обмен", "синхрон",
    "интеграц", "bx24", "b24", "http", "odata",
)


def augment_onec_calls(provider_id: str, allowed_tools: set[str], calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if provider_id != "mcp_1c" or "get_metadata_tree" not in allowed_tools:
        return calls
    existing = {str(row.get("id") or row.get("name") or "") for row in calls if isinstance(row, dict)}
    result = list(calls)
    for call in DISCOVERY_CALLS:
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


def _call_payload(calls: dict[str, Any], call_id: str) -> Any:
    row = calls.get(call_id)
    if not isinstance(row, dict) or row.get("success") is not True:
        return None
    return decode_mcp_result(row.get("result"))


def _clean_name(value: str) -> str:
    value = value.strip().strip("`*•-–—:;,. ")
    value = re.sub(r"^(Справочник|Документ|РегистрСведений|ПланОбмена|Обработка|ОбщийМодуль)[.:]", "", value, flags=re.I)
    return value.strip()


def _extract_names(value: Any) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()

    def add(raw: Any) -> None:
        if not isinstance(raw, str):
            return
        name = _clean_name(raw)
        key = name.casefold()
        if not name or key in seen or len(name) > 240:
            return
        if key in {"имя", "наименование", "объект", "объекты", "метаданные", "сводка"}:
            return
        seen.add(key)
        names.append(name)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("name", "Имя", "object", "Объект", "full_name", "fullName"):
                add(node.get(key))
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                if isinstance(child, str):
                    add(child)
                else:
                    walk(child)
        elif isinstance(node, str):
            for line in node.splitlines():
                line = line.strip()
                match = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(?:\*\*)?([^|()]+?)(?:\*\*)?(?:\s+[-—]|\s*\(|$)", line)
                if match:
                    add(match.group(1))
                    continue
                table = re.match(r"^\|\s*([^|]+?)\s*\|", line)
                if table and not re.match(r"^-+$", table.group(1).strip()):
                    add(table.group(1))

    walk(value)
    return names


def _bitrix_capabilities(bitrix: dict[str, Any]) -> dict[str, bool]:
    haystack = _text(bitrix).casefold()
    aliases = {
        "crm.company": ("crm.company", "company.list", "компани"),
        "crm.contact": ("crm.contact", "contact.list", "контакт"),
        "crm.deal": ("crm.deal", "deal.list", "сделк"),
        "crm.product": ("crm.product", "product.list", "товар", "product"),
        "crm.invoice": ("crm.invoice", "invoice.list", "счет", "счёт"),
    }
    return {entity: any(token in haystack for token in tokens) for entity, tokens in aliases.items()}


def _candidate_score(name: str, rule: dict[str, Any]) -> tuple[int, list[str]]:
    normalized = re.sub(r"[^a-zа-яё0-9]", "", name.casefold())
    score = 0
    reasons: list[str] = []
    for preferred in rule["preferred"]:
        target = re.sub(r"[^a-zа-яё0-9]", "", preferred.casefold())
        if normalized == target:
            score += 100
            reasons.append("точное имя типовой сущности")
        elif target and target in normalized:
            score += 45
            reasons.append(f"содержит {preferred}")
    for token in rule["tokens"]:
        compact = re.sub(r"[^a-zа-яё0-9]", "", token.casefold())
        if compact and compact in normalized:
            score += 18
            reasons.append(f"совпадение по маркеру «{token}»")
    return score, reasons


def _integration_artifacts(category_objects: dict[str, list[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category, names in category_objects.items():
        for name in names:
            lowered = name.casefold()
            matched = [token for token in INTEGRATION_TOKENS if token in lowered]
            if matched:
                rows.append({
                    "category": category,
                    "name": name,
                    "markers": matched[:5],
                    "status": "candidate",
                })
    return rows[:300]


def build_verification_pipeline(bitrix: dict[str, Any], onec: dict[str, Any]) -> dict[str, Any]:
    calls = onec.get("calls") if isinstance(onec.get("calls"), dict) else {}
    category_objects = {
        call["id"]: _extract_names(_call_payload(calls, call["id"]))
        for call in DISCOVERY_CALLS
    }
    discovery_ready = {
        call["id"]: bool(category_objects.get(call["id"]))
        for call in DISCOVERY_CALLS
    }
    bitrix_entities = _bitrix_capabilities(bitrix)
    mappings: list[dict[str, Any]] = []
    verification_calls: list[dict[str, Any]] = []

    for rule in ENTITY_RULES:
        names: list[str] = []
        for category in rule["categories"]:
            names.extend(category_objects.get(category, []))
        ranked = []
        for name in names:
            score, reasons = _candidate_score(name, rule)
            if score > 0:
                ranked.append({"name": name, "score": score, "reasons": reasons})
        ranked.sort(key=lambda row: (-row["score"], row["name"].casefold()))
        candidates = ranked[:8]
        top = candidates[0] if candidates else None
        second_score = candidates[1]["score"] if len(candidates) > 1 else 0
        onec_confirmed = bool(top and top["score"] >= 90 and top["score"] - second_score >= 20)
        bitrix_confirmed = bitrix_entities.get(rule["bitrix"], False)
        status = (
            "confirmed_candidate" if onec_confirmed and bitrix_confirmed
            else "candidate_found" if top
            else "discovery_required" if not all(discovery_ready.get(cat) for cat in rule["categories"])
            else "not_found"
        )
        selected = top["name"] if top else None
        mapping = {
            "id": rule["id"],
            "label": rule["label"],
            "bitrix_object": rule["bitrix"],
            "bitrix_evidence": bitrix_confirmed,
            "onec_type": rule["onec_type"],
            "onec_candidate": selected,
            "onec_evidence": onec_confirmed,
            "confidence": min(1.0, (top["score"] / 100.0)) if top else 0.0,
            "status": status,
            "candidates": candidates,
            "finding": False,
        }
        mappings.append(mapping)
        if selected:
            verification_calls.append({
                "id": f"structure_{rule['id']}",
                "name": "get_object_structure",
                "arguments": {"object_type": rule["onec_type"], "object_name": selected},
                "reason": f"Подтвердить структуру для связки {rule['label']}",
                "read_only": True,
            })

    artifacts = _integration_artifacts(category_objects)
    stages = [
        {
            "id": "discover_bitrix",
            "label": "Изучение Bitrix24",
            "status": "confirmed" if any(bitrix_entities.values()) else "insufficient_data",
            "facts": {"entities_confirmed": sum(bitrix_entities.values()), "entities_total": len(bitrix_entities)},
        },
        {
            "id": "discover_onec",
            "label": "Изучение 1С",
            "status": "confirmed" if all(discovery_ready.values()) else "partial",
            "facts": {"categories_loaded": sum(discovery_ready.values()), "categories_total": len(discovery_ready), "objects_loaded": sum(len(v) for v in category_objects.values())},
        },
        {
            "id": "detect_integration",
            "label": "Поиск точек интеграции",
            "status": "confirmed" if artifacts else "no_evidence",
            "facts": {"artifacts_found": len(artifacts)},
        },
        {
            "id": "validate_mapping",
            "label": "Проверка соответствия сущностей",
            "status": "in_progress" if mappings else "insufficient_data",
            "facts": {
                "confirmed_candidates": sum(row["status"] == "confirmed_candidate" for row in mappings),
                "candidates_found": sum(bool(row["onec_candidate"]) for row in mappings),
                "mappings_total": len(mappings),
            },
        },
        {"id": "validate_fields", "label": "Проверка полей", "status": "waiting_for_structure", "facts": {"planned_calls": len(verification_calls)}},
        {"id": "validate_data", "label": "Проверка данных", "status": "waiting_for_rules", "facts": {"configured_checks": 0}},
        {"id": "technical_conclusion", "label": "Техническое заключение", "status": "waiting_for_evidence", "facts": {"confirmed_findings": 0}},
    ]

    return {
        "version": VERSION,
        "mode": "read_only",
        "status": "mapping_in_progress" if any(discovery_ready.values()) else "discovery_required",
        "stages": stages,
        "bitrix_entities": bitrix_entities,
        "onec_discovery": {
            "categories": {key: {"loaded": discovery_ready[key], "objects": len(value)} for key, value in category_objects.items()},
            "objects_total": sum(len(value) for value in category_objects.values()),
        },
        "integration_artifacts": artifacts,
        "entity_mappings": mappings,
        "verification_calls": verification_calls,
        "findings": [],
        "technical_conclusion": {
            "status": "not_ready",
            "reason": "Заключение формируется только после подтверждения структур и правил сравнения данных.",
            "confirmed_findings": 0,
        },
        "execution_policy": {
            "bitrix_write": False,
            "onec_write": False,
            "mcp_write_tools": False,
            "proposal_only": True,
        },
    }
