from __future__ import annotations

import json
import re
from typing import Any


def _json_from_text(text: str) -> Any:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.I)
        value = re.sub(r"\s*```$", "", value)
    for _ in range(4):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            break
        if not isinstance(parsed, str):
            return parsed
        value = parsed.strip()
    starts = [pos for pos in (value.find("{"), value.find("[")) if pos >= 0]
    if starts:
        start = min(starts)
        for end_char in ("}", "]"):
            end = value.rfind(end_char)
            if end > start:
                try:
                    return json.loads(value[start : end + 1])
                except json.JSONDecodeError:
                    pass
    return text


def decode_mcp_result(value: Any) -> Any:
    """Normalize MCP tool results returned by different SDK/server versions."""
    for _ in range(8):
        if isinstance(value, str):
            decoded = _json_from_text(value)
            if decoded is value or decoded == value:
                return value
            value = decoded
            continue

        if isinstance(value, dict):
            if value.get("isError") is True:
                return value
            structured = value.get("structuredContent")
            if structured not in (None, {}, []):
                value = structured
                continue
            content = value.get("content")
            if isinstance(content, list):
                chunks: list[Any] = []
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "text" and isinstance(item.get("text"), str):
                        chunks.append(_json_from_text(item["text"]))
                    elif "data" in item:
                        chunks.append(item["data"])
                if len(chunks) == 1:
                    value = chunks[0]
                    continue
                if chunks:
                    return chunks
            if set(value).issubset({"result", "meta", "_meta"}) and "result" in value:
                value = value["result"]
                continue
            return value

        return value
    return value


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _find_configuration(value: Any) -> dict[str, Any]:
    aliases = {
        "name": ("name", "configuration", "configuration_name", "Имя", "Конфигурация"),
        "version": ("version", "configuration_version", "Версия"),
        "vendor": ("vendor", "provider", "Поставщик"),
        "platform_version": ("platform_version", "platformVersion", "ВерсияПлатформы"),
        "mode": ("mode", "work_mode", "Режим"),
    }
    best: dict[str, Any] = {}
    for node in _walk(value):
        candidate: dict[str, Any] = {}
        for target, names in aliases.items():
            for name in names:
                if name in node and node[name] not in (None, ""):
                    candidate[target] = node[name]
                    break
        if len(candidate) > len(best):
            best = candidate
    return best


CATEGORY_ALIASES = {
    "catalogs": ("Справочники", "Catalogs", "catalogs"),
    "documents": ("Документы", "Documents", "documents"),
    "information_registers": ("РегистрыСведений", "InformationRegisters", "information_registers"),
    "accumulation_registers": ("РегистрыНакопления", "AccumulationRegisters", "accumulation_registers"),
    "business_processes": ("БизнесПроцессы", "BusinessProcesses", "business_processes"),
    "tasks": ("Задачи", "Tasks", "tasks"),
    "exchange_plans": ("ПланыОбмена", "ExchangePlans", "exchange_plans"),
}


def _collection_count(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("count", "total", "Количество", "Всего"):
            number = value.get(key)
            if isinstance(number, (int, float)):
                return max(0, int(number))
        for key in ("items", "objects", "rows", "data", "result", "categories"):
            child = value.get(key)
            if isinstance(child, (list, dict)):
                return len(child)
        return len(value)
    return 0


def metadata_counts(value: Any) -> dict[str, int]:
    counts = {key: 0 for key in CATEGORY_ALIASES}
    normalized = {alias.lower(): target for target, aliases in CATEGORY_ALIASES.items() for alias in aliases}
    for node in _walk(value):
        for name, child in node.items():
            target = normalized.get(str(name).lower())
            if target:
                counts[target] = max(counts[target], _collection_count(child))
        label = node.get("name") or node.get("category") or node.get("Категория")
        if isinstance(label, str):
            target = normalized.get(label.lower())
            if target:
                counts[target] = max(counts[target], _collection_count(node))
                for key in ("count", "total", "Количество", "Всего"):
                    if isinstance(node.get(key), (int, float)):
                        counts[target] = max(counts[target], int(node[key]))
    return counts


def record_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("count", "total", "Количество", "Всего"):
            if isinstance(value.get(key), (int, float)):
                return max(0, int(value[key]))
        for key in ("items", "rows", "events", "records", "data", "result", "objects", "orphans"):
            child = value.get(key)
            if isinstance(child, (list, dict)):
                return len(child)
    return 0


def build_onec_profile(configuration: Any, metadata: Any, errors: Any, warnings: Any, subsystems: Any) -> dict[str, Any]:
    config = _find_configuration(configuration)
    counts = metadata_counts(metadata)
    return {
        "status": "confirmed" if config or configuration is not None else "insufficient_data",
        "configuration": config,
        "metadata_counts": counts,
        "metadata_total": sum(counts.values()),
        "event_log": {
            "errors": record_count(errors),
            "warnings": record_count(warnings),
        },
        "subsystems": {
            "analyzed_items": record_count(subsystems),
        },
        "parser": {
            "version": "4.3.2",
            "configuration_decoded": bool(config),
            "metadata_decoded": any(counts.values()),
        },
    }
