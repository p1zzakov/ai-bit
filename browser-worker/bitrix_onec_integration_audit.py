from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "4.3.1"
DEFAULT_MAP = [
    {"id":"company_counterparty","bitrix":"crm.company","onec":"Catalog.Контрагенты","label":"Компания ↔ Контрагент"},
    {"id":"contact_person","bitrix":"crm.contact","onec":"Catalog.КонтактныеЛица","label":"Контакт ↔ Контактное лицо"},
    {"id":"deal_order","bitrix":"crm.deal","onec":"Document.ЗаказКлиента","label":"Сделка ↔ Заказ клиента"},
    {"id":"product_nomenclature","bitrix":"crm.product","onec":"Catalog.Номенклатура","label":"Товар ↔ Номенклатура"},
    {"id":"invoice_customer","bitrix":"crm.invoice","onec":"Document.СчетНаОплатуПокупателю","label":"Счёт ↔ Счёт покупателю"},
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _json_env(name: str, default: Any) -> Any:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def _contains(data: Any, tokens: list[str]) -> bool:
    haystack = _text(data).lower()
    return any(token.lower() in haystack for token in tokens if token)


def _latest_bitrix(root: Path) -> dict[str, Any]:
    candidates = [
        root / "deep-rest-evidence" / "latest.json",
        root / "capability-discovery" / "latest.json",
        root / "business-architecture" / "latest.json",
        root / "evidence-audit" / "latest.json",
    ]
    return {path.parent.name: _read(path) for path in candidates if path.exists()}


def _latest_onec(root: Path) -> dict[str, Any]:
    external = _read(root / "external-sources" / "latest.json")
    providers = external.get("providers") if isinstance(external.get("providers"), list) else []
    for provider in providers:
        if not isinstance(provider, dict):
            continue
        server_name = _text(provider.get("server")).lower()
        if provider.get("id") == "mcp_1c" or "mcp-1c" in server_name or "1c" in str(provider.get("name", "")).lower():
            return provider
    return {}


def _tool_calls(onec: dict[str, Any]) -> dict[str, Any]:
    calls = onec.get("calls")
    return calls if isinstance(calls, dict) else {}


def _call(calls: dict[str, Any], call_id: str, tool: str | None = None) -> dict[str, Any]:
    value = calls.get(call_id)
    if isinstance(value, dict):
        return value
    if tool:
        for row in calls.values():
            if isinstance(row, dict) and row.get("tool") == tool:
                return row
    return {}


def _decode_mcp_result(value: Any) -> Any:
    if isinstance(value, dict) and isinstance(value.get("content"), list):
        texts = [row.get("text") for row in value["content"] if isinstance(row, dict) and isinstance(row.get("text"), str)]
        if texts:
            joined = "\n".join(texts)
            try:
                return json.loads(joined)
            except json.JSONDecodeError:
                return joined
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _payload(calls: dict[str, Any], call_id: str, tool: str | None = None) -> Any:
    row = _call(calls, call_id, tool)
    if not row.get("success"):
        return None
    return _decode_mcp_result(row.get("result"))


def _count_named_collections(value: Any) -> dict[str, int]:
    aliases = {
        "catalogs": ("Справочники", "Catalogs", "catalogs"),
        "documents": ("Документы", "Documents", "documents"),
        "information_registers": ("РегистрыСведений", "InformationRegisters", "information_registers"),
        "accumulation_registers": ("РегистрыНакопления", "AccumulationRegisters", "accumulation_registers"),
        "business_processes": ("БизнесПроцессы", "BusinessProcesses", "business_processes"),
        "tasks": ("Задачи", "Tasks", "tasks"),
        "exchange_plans": ("ПланыОбмена", "ExchangePlans", "exchange_plans"),
    }
    counts = {key: 0 for key in aliases}
    for node in _walk(value):
        for key, names in aliases.items():
            for name in names:
                collection = node.get(name)
                if isinstance(collection, (list, dict)):
                    counts[key] = max(counts[key], len(collection))
    return counts


def _list_size(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("items", "rows", "events", "data", "result", "objects"):
            child = value.get(key)
            if isinstance(child, (list, dict)):
                return len(child)
        return len(value)
    return 0


def _source_evidence(onec: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    calls = _tool_calls(onec)
    specs = [
        ("configuration", "get_configuration_info", "Конфигурация 1С"),
        ("metadata_summary", "get_metadata_tree", "Дерево метаданных"),
        ("onec_event_log_errors", "get_event_log", "Журнал ошибок"),
        ("onec_event_log_warnings", "get_event_log", "Журнал предупреждений"),
        ("subsystem_orphans", "analyze_subsystems", "Анализ подсистем"),
    ]
    rows = []
    for call_id, tool, label in specs:
        call = _call(calls, call_id, tool)
        success = call.get("success") is True
        rows.append({
            "id": call_id,
            "tool": tool,
            "label": label,
            "status": "confirmed" if success else "error" if call else "insufficient_data",
            "duration_ms": call.get("duration_ms"),
            "error": call.get("error"),
        })

    configuration = _payload(calls, "configuration", "get_configuration_info")
    metadata = _payload(calls, "metadata_summary", "get_metadata_tree")
    errors = _payload(calls, "onec_event_log_errors")
    warnings = _payload(calls, "onec_event_log_warnings")
    subsystems = _payload(calls, "subsystem_orphans", "analyze_subsystems")
    profile = {
        "status": "confirmed" if configuration is not None else "insufficient_data",
        "configuration": configuration if isinstance(configuration, dict) else {},
        "metadata_counts": _count_named_collections(metadata),
        "event_log": {"errors": _list_size(errors), "warnings": _list_size(warnings)},
        "subsystems": {"analyzed_items": _list_size(subsystems)},
    }
    return rows, profile


def _mapping_rows(bitrix: dict[str, Any], onec: dict[str, Any]) -> list[dict[str, Any]]:
    mappings = _json_env("BITRIX_ONEC_ENTITY_MAP_JSON", DEFAULT_MAP)
    if not isinstance(mappings, list):
        mappings = DEFAULT_MAP
    calls = _tool_calls(onec)
    metadata = _payload(calls, "metadata_summary", "get_metadata_tree")
    rows = []
    for raw in mappings:
        if not isinstance(raw, dict):
            continue
        bx = str(raw.get("bitrix") or "")
        oc = str(raw.get("onec") or "")
        bx_found = bool(bitrix) and _contains(bitrix, [bx, bx.split(".")[-1]])
        oc_found = metadata is not None and _contains(metadata, [oc, oc.split(".")[-1]])
        status = "confirmed" if bx_found and oc_found else "unverified" if bx_found or oc_found else "insufficient_data"
        rows.append({
            "id": raw.get("id") or f"map-{len(rows)+1}",
            "label": raw.get("label") or f"{bx} ↔ {oc}",
            "bitrix_object": bx,
            "onec_object": oc,
            "bitrix_evidence": bx_found,
            "onec_evidence": oc_found,
            "status": status,
            "is_finding": False,
            "note": "Маппинг требует подтверждения с обеих сторон; отсутствие evidence не является дефектом.",
        })
    return rows


def _field_rules(bitrix: dict[str, Any], onec: dict[str, Any]) -> list[dict[str, Any]]:
    rules = _json_env("BITRIX_ONEC_FIELD_MAP_JSON", [])
    if not isinstance(rules, list):
        rules = []
    calls = _tool_calls(onec)
    rows = []
    for raw in rules:
        if not isinstance(raw, dict):
            continue
        bx_field = str(raw.get("bitrix_field") or "")
        oc_field = str(raw.get("onec_field") or "")
        bx_found = bool(bitrix) and _contains(bitrix, [bx_field])
        oc_found = _contains(calls, [oc_field]) if calls else False
        status = "confirmed" if bx_found and oc_found else "unverified" if bx_found or oc_found else "insufficient_data"
        rows.append({
            "entity": raw.get("entity") or "",
            "bitrix_field": bx_field,
            "onec_field": oc_field,
            "bitrix_evidence": bx_found,
            "onec_evidence": oc_found,
            "status": status,
            "is_finding": False,
        })
    return rows


def _sync_evidence(bitrix: dict[str, Any], onec: dict[str, Any]) -> dict[str, Any]:
    calls = _tool_calls(onec)
    logs = [_payload(calls, "onec_event_log_errors"), _payload(calls, "onec_event_log_warnings")]
    available = [value for value in logs if value is not None]
    tokens = ["обмен", "bitrix", "битрикс", "синхрон", "http", "rest"]
    matches = []
    for log in available:
        for node in _walk(log):
            text = _text(node)
            if any(token in text.lower() for token in tokens):
                matches.append(node)
            if len(matches) >= 100:
                break
    status = "confirmed" if matches else "no_matching_events" if available else "insufficient_data"
    return {
        "status": status,
        "bitrix_snapshot_available": bool(bitrix),
        "onec_event_log_available": bool(available),
        "matching_events": matches,
        "matching_events_count": len(matches),
        "note": "Отсутствие совпадений в выбранной выборке журнала не доказывает отсутствие интеграции.",
    }


def _data_checks(onec: dict[str, Any]) -> list[dict[str, Any]]:
    configured = _json_env("BITRIX_ONEC_DATA_CHECKS_JSON", [])
    if not isinstance(configured, list):
        configured = []
    calls = _tool_calls(onec)
    rows = []
    for check in configured:
        if not isinstance(check, dict):
            continue
        call_id = str(check.get("onec_call_id") or "")
        evidence = calls.get(call_id)
        success = isinstance(evidence, dict) and evidence.get("success") is True
        rows.append({
            "id": check.get("id") or call_id,
            "label": check.get("label") or call_id,
            "bitrix_source": check.get("bitrix_source"),
            "onec_call_id": call_id,
            "status": "confirmed" if success else "insufficient_data",
            "evidence": evidence,
        })
    return rows


def _required_calls() -> list[dict[str, Any]]:
    return [
        {"id":"configuration","name":"get_configuration_info","arguments":{}},
        {"id":"metadata_summary","name":"get_metadata_tree","arguments":{}},
        {"id":"onec_event_log_errors","name":"get_event_log","arguments":{"level":"Ошибка","limit":200}},
        {"id":"onec_event_log_warnings","name":"get_event_log","arguments":{"level":"Предупреждение","limit":200}},
        {"id":"subsystem_orphans","name":"analyze_subsystems","arguments":{"action":"orphans"}},
    ]


def build_integration_audit(root: Path) -> dict[str, Any]:
    bitrix = _latest_bitrix(root)
    onec = _latest_onec(root)
    source_evidence, onec_profile = _source_evidence(onec)
    topology = _mapping_rows(bitrix, onec)
    fields = _field_rules(bitrix, onec)
    synchronization = _sync_evidence(bitrix, onec)
    data_checks = _data_checks(onec)

    source_confirmed = sum(1 for row in source_evidence if row["status"] == "confirmed")
    source_errors = sum(1 for row in source_evidence if row["status"] == "error")
    mapping_confirmed = sum(1 for row in [*topology, *fields, *data_checks] if row.get("status") == "confirmed")
    mapping_unverified = sum(1 for row in [*topology, *fields] if row.get("status") == "unverified")
    insufficient = sum(1 for row in [*topology, *fields, *data_checks] if row.get("status") == "insufficient_data")

    findings: list[dict[str, Any]] = []
    blueprint: list[dict[str, Any]] = []
    overall = "ready_for_mapping" if source_confirmed == len(source_evidence) else "attention" if source_confirmed else "insufficient_data"
    payload = {
        "version": VERSION,
        "generated_at": _now(),
        "mode": "read_only",
        "status": overall,
        "sources": {"bitrix": bool(bitrix), "onec_mcp": bool(onec)},
        "summary": {
            "source_checks_confirmed": source_confirmed,
            "source_checks_total": len(source_evidence),
            "source_errors": source_errors,
            "mappings_confirmed": mapping_confirmed,
            "mappings_unverified": mapping_unverified,
            "insufficient_data": insufficient,
            "findings": 0,
        },
        "source_evidence": source_evidence,
        "onec_profile": onec_profile,
        "topology": topology,
        "field_integrity": fields,
        "data_integrity": data_checks,
        "synchronization": synchronization,
        "findings": findings,
        "implementation_blueprint": blueprint,
        "required_mcp_calls": _required_calls(),
        "execution_policy": {"bitrix_write": False, "onec_write": False, "rest_execution": False, "mcp_write_tools": False, "proposals_only": True},
    }
    folder = root / "bitrix-onec-integration"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def latest_integration_audit(root: Path) -> dict[str, Any]:
    path = root / "bitrix-onec-integration" / "latest.json"
    return _read(path) or build_integration_audit(root)
