from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, parse, request

VERSION = "2.0.0-alpha.4"

PROBES: dict[str, tuple[str, dict[str, Any]]] = {
    "crm_types": ("crm.type.list", {}),
    "crm_categories": ("crm.category.list", {"entityTypeId": 2}),
    "crm_statuses": ("crm.status.list", {}),
    "crm_deals": ("crm.deal.list", {"select": ["ID", "TITLE", "CATEGORY_ID", "STAGE_ID", "DATE_CREATE"], "start": 0}),
    "bizproc_templates": ("bizproc.workflow.template.list", {}),
    "bizproc_instances": ("bizproc.workflow.instances", {}),
    "lists": ("lists.get", {}),
    "crm_forms": ("crm.webform.list", {}),
    "disk_storages": ("disk.storage.getlist", {}),
}

CAPABILITY_PATTERNS: dict[str, list[str]] = {
    "electronic_document_exchange": [r"электронн.{0,20}документ", r"\bэдо\b", r"document exchange", r"диадок", r"сбис"],
    "contract_approval": [r"согласовани.{0,25}договор", r"договор.{0,25}согласован", r"contract approval"],
    "internal_memos": [r"служебн.{0,15}записк", r"служебка", r"internal memo"],
    "user_provisioning_request": [r"создани.{0,25}пользовател", r"нов.{0,12}сотрудник.{0,30}(ad|1с)", r"заявк.{0,25}(ad|1с)"],
    "business_processes": [r"bizproc", r"workflow", r"бизнес[- ]?процесс"],
    "employee_onboarding": [r"при.м.{0,20}сотрудник", r"адаптац.{0,20}сотрудник", r"onboarding"],
    "employee_offboarding": [r"увольнен", r"отзыв.{0,20}доступ", r"offboarding"],
    "leave_requests": [r"заявк.{0,20}отпуск", r"график.{0,20}отпуск", r"отсутстви"],
    "business_trips": [r"командиров", r"business trip"],
    "it_service_requests": [r"заявк.{0,20}(ит|it|техподдерж)", r"helpdesk", r"service desk"],
    "access_requests": [r"заявк.{0,20}доступ", r"изменени.{0,20}прав"],
    "purchase_requests": [r"заявк.{0,20}закуп", r"purchase request"],
    "payment_approval": [r"согласовани.{0,20}оплат", r"заявк.{0,20}оплат"],
    "repair_requests": [r"заявк.{0,20}ремонт", r"обслуживан.{0,20}оборудован", r"maintenance"],
    "knowledge_base": [r"база знан", r"knowledge", r"регламент"],
}


def _call(base_url: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/" + method
    body = parse.urlencode({"params": json.dumps(payload, ensure_ascii=False)}).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with request.urlopen(req, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, dict) and data.get("error"):
            return {"ok": False, "method": method, "error": data.get("error"), "error_description": data.get("error_description")}
        return {"ok": True, "method": method, "result": data.get("result") if isinstance(data, dict) else data, "total": data.get("total") if isinstance(data, dict) else None}
    except error.HTTPError as exc:
        return {"ok": False, "method": method, "error": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"ok": False, "method": method, "error": f"{type(exc).__name__}: {exc}"}


def _flatten(value: Any, out: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            out.append(str(key))
            _flatten(item, out)
    elif isinstance(value, list):
        for item in value[:1000]:
            _flatten(item, out)
    elif value is not None:
        out.append(str(value))


def collect_deep_rest_evidence(artifacts_dir: Path) -> dict[str, Any]:
    base_url = os.getenv("BITRIX_WEBHOOK_URL", "").strip()
    probes: dict[str, Any] = {}
    if base_url:
        for probe_id, (method, payload) in PROBES.items():
            probes[probe_id] = _call(base_url, method, payload)
    parts: list[str] = []
    for probe in probes.values():
        if probe.get("ok"):
            _flatten(probe.get("result"), parts)
    corpus = re.sub(r"\s+", " ", " ".join(parts)).lower()
    capabilities: dict[str, Any] = {}
    successful_probes = [key for key, value in probes.items() if value.get("ok")]
    for capability_id, patterns in CAPABILITY_PATTERNS.items():
        matches: list[str] = []
        for pattern in patterns:
            found = re.search(pattern, corpus, re.IGNORECASE)
            if found:
                matches.append(found.group(0)[:160])
        capabilities[capability_id] = {
            "positive": bool(matches),
            "evidence": matches[:10],
            "checked_probes": successful_probes,
            "confidence": 0.9 if matches else (0.72 if len(successful_probes) >= 5 else 0.25),
        }
    result = {
        "version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "configured": bool(base_url),
        "summary": {
            "total_probes": len(PROBES),
            "successful_probes": len(successful_probes),
            "failed_probes": len(PROBES) - len(successful_probes),
            "positive_capabilities": sum(1 for row in capabilities.values() if row["positive"]),
        },
        "probes": probes,
        "capabilities": capabilities,
        "method": "Read-only Bitrix24 REST inspection. Failed or unavailable methods never prove absence.",
    }
    folder = artifacts_dir / "deep-rest-evidence"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def read_latest_deep_rest_evidence(artifacts_dir: Path) -> dict[str, Any]:
    path = artifacts_dir / "deep-rest-evidence" / "latest.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise FileNotFoundError(path)
