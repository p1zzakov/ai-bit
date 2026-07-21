from __future__ import annotations

import json
import re
from typing import Any

PARSER_VERSION = "4.3.3"


def _json_from_text(text: str) -> Any:
    value = text.strip()

    fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", value, flags=re.I | re.S)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

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
            if decoded == value:
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


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-zа-яё0-9]", "", value.lower().replace("ё", "е"))


def _markdown_pairs(text: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    patterns = (
        r"^\s*[-*]?\s*\*\*(.+?)\*\*\s*[:—-]\s*(.+?)\s*$",
        r"^\s*[-*]?\s*([^:#]{2,80})\s*:\s*(.+?)\s*$",
        r"^\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$",
    )
    for line in text.splitlines():
        for pattern in patterns:
            match = re.match(pattern, line)
            if not match:
                continue
            key = match.group(1).strip(" *|`")
            val = match.group(2).strip(" *|`")
            if key and val and not set(key) <= {"-"}:
                pairs[_normalize_label(key)] = val
            break
    return pairs


def _find_configuration(value: Any) -> dict[str, Any]:
    aliases = {
        "name": ("name", "configuration", "configuration_name", "Имя", "Конфигурация", "Название конфигурации"),
        "version": ("version", "configuration_version", "Версия", "Версия конфигурации"),
        "vendor": ("vendor", "provider", "Поставщик", "Разработчик"),
        "platform_version": ("platform_version", "platformVersion", "ВерсияПлатформы", "Версия платформы", "Платформа"),
        "mode": ("mode", "work_mode", "Режим", "Режим работы"),
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

    texts: list[str] = []
    if isinstance(value, str):
        texts.append(value)
    elif isinstance(value, list):
        texts.extend(item for item in value if isinstance(item, str))

    normalized_aliases = {
        target: {_normalize_label(name) for name in names}
        for target, names in aliases.items()
    }
    for text in texts:
        pairs = _markdown_pairs(text)
        candidate = dict(best)
        for target, names in normalized_aliases.items():
            for name in names:
                if name in pairs and pairs[name]:
                    candidate[target] = pairs[name]
                    break
        if len(candidate) > len(best):
            best = candidate
    return best


CATEGORY_ALIASES = {
    "catalogs": ("Справочники", "Catalogs", "catalogs"),
    "documents": ("Документы", "Documents", "documents"),
    "information_registers": ("РегистрыСведений", "Регистры сведений", "InformationRegisters", "information_registers"),
    "accumulation_registers": ("РегистрыНакопления", "Регистры накопления", "AccumulationRegisters", "accumulation_registers"),
    "business_processes": ("БизнесПроцессы", "Бизнес-процессы", "Бизнес процессы", "BusinessProcesses", "business_processes"),
    "tasks": ("Задачи", "Tasks", "tasks"),
    "exchange_plans": ("ПланыОбмена", "Планы обмена", "ExchangePlans", "exchange_plans"),
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


def _markdown_metadata_counts(text: str) -> dict[str, int]:
    counts = {key: 0 for key in CATEGORY_ALIASES}
    normalized = {
        _normalize_label(alias): target
        for target, aliases in CATEGORY_ALIASES.items()
        for alias in aliases
    }
    pattern = re.compile(r"^\s*[-*]\s*\*\*(.+?)\*\*\s*\((\d+)\)", re.M)
    for label, number in pattern.findall(text):
        target = normalized.get(_normalize_label(label))
        if target:
            counts[target] = max(counts[target], int(number))
    return counts


def metadata_counts(value: Any) -> dict[str, int]:
    counts = {key: 0 for key in CATEGORY_ALIASES}
    normalized = {
        _normalize_label(alias): target
        for target, aliases in CATEGORY_ALIASES.items()
        for alias in aliases
    }
    for node in _walk(value):
        for name, child in node.items():
            target = normalized.get(_normalize_label(str(name)))
            if target:
                counts[target] = max(counts[target], _collection_count(child))
        label = node.get("name") or node.get("category") or node.get("Категория")
        if isinstance(label, str):
            target = normalized.get(_normalize_label(label))
            if target:
                counts[target] = max(counts[target], _collection_count(node))
                for key in ("count", "total", "Количество", "Всего"):
                    if isinstance(node.get(key), (int, float)):
                        counts[target] = max(counts[target], int(node[key]))

    texts: list[str] = []
    if isinstance(value, str):
        texts.append(value)
    elif isinstance(value, list):
        texts.extend(item for item in value if isinstance(item, str))
    for text in texts:
        parsed = _markdown_metadata_counts(text)
        for key, number in parsed.items():
            counts[key] = max(counts[key], number)
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
    if isinstance(value, str):
        for pattern in (
            r"(?:Найдено|Всего|Количество)\D{0,30}(\d+)",
            r"^\s*[-*]\s+.+$",
        ):
            matches = re.findall(pattern, value, flags=re.I | re.M)
            if matches:
                if pattern.endswith("$"):
                    return len(matches)
                return int(matches[0])
    return 0


def _raw_format(value: Any) -> str:
    if isinstance(value, str):
        if re.search(r"^\s*#|\*\*.+?\*\*", value, flags=re.M):
            return "markdown"
        return "text"
    if isinstance(value, dict):
        return "json_object"
    if isinstance(value, list):
        return "json_array"
    if value is None:
        return "none"
    return type(value).__name__


def build_onec_profile(configuration: Any, metadata: Any, errors: Any, warnings: Any, subsystems: Any) -> dict[str, Any]:
    config = _find_configuration(configuration)
    counts = metadata_counts(metadata)
    config_decoded = bool(config)
    metadata_decoded = any(counts.values())
    payload_decoded = config_decoded and metadata_decoded
    return {
        "status": "confirmed" if payload_decoded else "partial" if configuration is not None or metadata is not None else "insufficient_data",
        "transport_confirmed": configuration is not None and metadata is not None,
        "payload_decoded": payload_decoded,
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
            "version": PARSER_VERSION,
            "configuration_decoded": config_decoded,
            "metadata_decoded": metadata_decoded,
            "raw_format": {
                "configuration": _raw_format(configuration),
                "metadata": _raw_format(metadata),
                "errors": _raw_format(errors),
                "warnings": _raw_format(warnings),
                "subsystems": _raw_format(subsystems),
            },
        },
    }
