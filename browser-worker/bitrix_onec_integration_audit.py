from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "4.3.0"
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


def _tool_payload(calls: dict[str, Any], tool: str) -> Any:
    for key, value in calls.items():
        if not isinstance(value, dict):
            continue
        if key == tool or value.get("tool") == tool or value.get("name") == tool:
            return value.get("result")
    return None


def _mapping_rows(bitrix: dict[str, Any], onec: dict[str, Any]) -> list[dict[str, Any]]:
    mappings = _json_env("BITRIX_ONEC_ENTITY_MAP_JSON", DEFAULT_MAP)
    if not isinstance(mappings, list):
        mappings = DEFAULT_MAP
    onec_calls = _tool_calls(onec)
    metadata = _tool_payload(onec_calls, "get_metadata_tree") or onec_calls
    rows = []
    for raw in mappings:
        if not isinstance(raw, dict):
            continue
        bx = str(raw.get("bitrix") or "")
        oc = str(raw.get("onec") or "")
        bx_tokens = [bx, bx.split(".")[-1]]
        oc_tokens = [oc, oc.split(".")[-1]]
        bx_found = bool(bitrix) and _contains(bitrix, bx_tokens)
        oc_found = bool(onec) and _contains(metadata, oc_tokens)
        if bx_found and oc_found:
            status = "confirmed"
        elif bx_found or oc_found:
            status = "partial"
        else:
            status = "insufficient_data"
        rows.append({
            "id": raw.get("id") or f"map-{len(rows)+1}",
            "label": raw.get("label") or f"{bx} ↔ {oc}",
            "bitrix_object": bx,
            "onec_object": oc,
            "bitrix_evidence": bx_found,
            "onec_evidence": oc_found,
            "status": status,
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
        oc_found = bool(onec) and _contains(calls, [oc_field])
        rows.append({
            "entity": raw.get("entity") or "",
            "bitrix_field": bx_field,
            "onec_field": oc_field,
            "bitrix_evidence": bx_found,
            "onec_evidence": oc_found,
            "status": "confirmed" if bx_found and oc_found else "partial" if bx_found or oc_found else "insufficient_data",
        })
    return rows


def _sync_evidence(bitrix: dict[str, Any], onec: dict[str, Any]) -> dict[str, Any]:
    calls = _tool_calls(onec)
    logs = _tool_payload(calls, "get_event_log")
    tokens = ["обмен", "bitrix", "битрикс", "синхрон", "http", "rest"]
    bx_has = bool(bitrix)
    log_has = logs is not None
    matches = []
    if logs is not None:
        for node in _walk(logs):
            text = _text(node)
            if any(token in text.lower() for token in tokens):
                matches.append(node)
            if len(matches) >= 100:
                break
    return {
        "status": "confirmed" if matches else "partial" if bx_has and log_has else "insufficient_data",
        "bitrix_snapshot_available": bx_has,
        "onec_event_log_available": log_has,
        "matching_events": matches,
        "matching_events_count": len(matches),
        "note": "Состояние очереди и фактическая задержка подтверждаются только событиями или регистрами обмена.",
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
        rows.append({
            "id": check.get("id") or call_id,
            "label": check.get("label") or call_id,
            "bitrix_source": check.get("bitrix_source"),
            "onec_call_id": call_id,
            "status": "confirmed" if evidence else "insufficient_data",
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
    topology = _mapping_rows(bitrix, onec)
    fields = _field_rules(bitrix, onec)
    synchronization = _sync_evidence(bitrix, onec)
    data_checks = _data_checks(onec)
    confirmed = sum(1 for row in [*topology, *fields, *data_checks] if row.get("status") == "confirmed")
    partial = sum(1 for row in [*topology, *fields, *data_checks] if row.get("status") == "partial")
    insufficient = sum(1 for row in [*topology, *fields, *data_checks] if row.get("status") == "insufficient_data")
    findings = []
    for row in topology:
        if row["status"] == "partial":
            findings.append({"severity":"high","area":"topology","title":row["label"],"fact":"Объект подтверждён только в одной системе.","evidence":row,"action":"Проверить настройку соответствия и маршрут обмена."})
    for row in fields:
        if row["status"] == "partial":
            findings.append({"severity":"high","area":"fields","title":f"Поле {row['bitrix_field']} ↔ {row['onec_field']}","fact":"Поле подтверждено только с одной стороны.","evidence":row,"action":"Уточнить маппинг и обязательность поля."})
    blueprint = [{
        "priority": index + 1,
        "area": item["area"],
        "task": item["action"],
        "basis": item["fact"],
        "acceptance": "Повторный аудит подтверждает объект или поле в обеих системах.",
        "execution": "proposal_only",
    } for index, item in enumerate(findings)]
    overall = "ready" if confirmed and not partial else "attention" if confirmed or partial else "insufficient_data"
    payload = {
        "version": VERSION,
        "generated_at": _now(),
        "mode": "read_only",
        "status": overall,
        "sources": {"bitrix": bool(bitrix), "onec_mcp": bool(onec)},
        "summary": {"confirmed": confirmed, "partial": partial, "insufficient_data": insufficient, "findings": len(findings)},
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
