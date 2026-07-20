from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "2.0.0-alpha.2"


def _read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _latest_crawl(artifacts_dir: Path) -> dict[str, Any]:
    for path in sorted((artifacts_dir / "history").glob("*.json"), reverse=True):
        data = _read(path)
        if data:
            return data
    return {}


def _flatten(value: Any, parts: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            parts.append(str(key))
            _flatten(item, parts)
    elif isinstance(value, list):
        for item in value[:500]:
            _flatten(item, parts)
    elif value is not None:
        parts.append(str(value))


def _corpus(artifacts_dir: Path) -> str:
    sources = [
        _latest_crawl(artifacts_dir),
        _read(artifacts_dir / "business-architecture" / "latest.json"),
        _read(artifacts_dir / "process-mining" / "latest.json"),
        _read(artifacts_dir / "operations" / "latest.json"),
    ]
    parts: list[str] = []
    for source in sources:
        _flatten(source, parts)
    return re.sub(r"\s+", " ", " ".join(parts)).lower()


RULES: dict[str, dict[str, Any]] = {
    "business_processes": {
        "implemented": [r"бизнес[- ]?процесс", r"workflow", r"bizproc", r"шаблон.{0,20}процесс"],
        "strong": [r"запущен.{0,25}процесс", r"экземпляр.{0,20}процесс", r"автоматизац"],
    },
    "contract_approval": {
        "implemented": [r"согласовани.{0,20}договор", r"договор.{0,25}согласован", r"contract.{0,20}approval"],
        "strong": [r"маршрут.{0,20}договор", r"стадия.{0,20}договор", r"робот.{0,20}договор"],
    },
    "internal_memos": {
        "implemented": [r"служебн.{0,12}записк", r"служебка", r"internal memo"],
        "strong": [r"реестр.{0,20}служеб", r"маршрут.{0,20}служеб"],
    },
    "user_provisioning_request": {
        "implemented": [r"создани.{0,20}пользовател", r"нов.{0,10}сотрудник.{0,30}(ad|1с)", r"заявк.{0,30}(ad|1с)"],
        "strong": [r"выдач.{0,15}доступ", r"onboarding", r"при.м.{0,20}сотрудник"],
    },
    "electronic_document_exchange": {
        "implemented": [r"электронн.{0,20}документооборот", r"эдо", r"обмен.{0,20}документ"],
        "strong": [r"диадок", r"сбис", r"edo", r"подписан.{0,20}документ"],
    },
    "employee_onboarding": {
        "implemented": [r"при.м.{0,20}сотрудник", r"адаптац.{0,20}сотрудник", r"onboarding"],
        "strong": [r"чек[- ]?лист.{0,20}нов.{0,10}сотрудник"],
    },
    "employee_offboarding": {
        "implemented": [r"увольнен", r"отзыв.{0,20}доступ", r"offboarding"],
        "strong": [r"блокировк.{0,20}(ad|1с|учетн)"],
    },
    "leave_requests": {
        "implemented": [r"заявк.{0,20}отпуск", r"график.{0,20}отпуск", r"отсутстви"],
        "strong": [r"согласовани.{0,20}отпуск"],
    },
    "business_trips": {
        "implemented": [r"командиров", r"business trip"],
        "strong": [r"авансов.{0,20}отч", r"согласовани.{0,20}командиров"],
    },
    "it_service_requests": {
        "implemented": [r"заявк.{0,20}(ит|it|техподдерж)", r"helpdesk", r"service desk"],
        "strong": [r"sla", r"очеред.{0,20}поддерж"],
    },
    "access_requests": {
        "implemented": [r"заявк.{0,20}доступ", r"изменени.{0,20}прав"],
        "strong": [r"согласовани.{0,20}доступ"],
    },
    "purchase_requests": {
        "implemented": [r"заявк.{0,20}закуп", r"purchase request", r"потребност.{0,20}закуп"],
        "strong": [r"согласовани.{0,20}закуп"],
    },
    "payment_approval": {
        "implemented": [r"согласовани.{0,20}оплат", r"заявк.{0,20}оплат", r"payment approval"],
        "strong": [r"платежн.{0,20}календар"],
    },
    "repair_requests": {
        "implemented": [r"заявк.{0,20}ремонт", r"обслуживан.{0,20}оборудован", r"maintenance"],
        "strong": [r"планов.{0,20}ремонт"],
    },
    "knowledge_base": {
        "implemented": [r"база знан", r"регламент", r"knowledge"],
        "strong": [r"инструкц", r"статья.{0,20}знан"],
    },
}


def _matches(text: str, patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            found.append(match.group(0)[:160])
    return found


def discover_capabilities(artifacts_dir: Path) -> dict[str, Any]:
    text = _corpus(artifacts_dir)
    capabilities: dict[str, dict[str, Any]] = {}
    for capability_id, rule in RULES.items():
        base = _matches(text, rule.get("implemented", []))
        strong = _matches(text, rule.get("strong", []))
        if base and strong:
            status, confidence = "implemented", 0.9
        elif base:
            status, confidence = "partial", 0.65
        else:
            status, confidence = "unknown", 0.2
        capabilities[capability_id] = {
            "status": status,
            "confidence": confidence,
            "evidence": (base + strong)[:8],
            "source": "automatic_discovery",
        }

    result = {
        "version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "capabilities": capabilities,
        "summary": {
            "implemented": sum(1 for row in capabilities.values() if row["status"] == "implemented"),
            "partial": sum(1 for row in capabilities.values() if row["status"] == "partial"),
            "unknown": sum(1 for row in capabilities.values() if row["status"] == "unknown"),
        },
        "method": "Evidence is discovered from current crawl, architecture, process-mining and operations artifacts. Unknown is never treated as missing.",
    }
    folder = artifacts_dir / "capability-discovery"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def read_latest_capability_discovery(artifacts_dir: Path) -> dict[str, Any]:
    data = _read(artifacts_dir / "capability-discovery" / "latest.json")
    if not data:
        raise FileNotFoundError("Capability discovery has not been collected")
    return data
