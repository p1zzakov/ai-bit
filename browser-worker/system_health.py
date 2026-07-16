from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_provider import ai_status
from operational_intelligence import rest_call


def _now() -> datetime:
    return datetime.now(UTC)


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _age_hours(value: Any) -> float | None:
    dt = _parse_dt(value)
    if dt is None:
        return None
    return round(max(0.0, (_now() - dt).total_seconds() / 3600), 1)


def _freshness(name: str, generated_at: Any, *, warn_hours: int, stale_hours: int) -> dict[str, Any]:
    age = _age_hours(generated_at)
    if age is None:
        return {"name": name, "status": "missing", "generated_at": generated_at, "age_hours": None, "message": "Данные отсутствуют"}
    status = "ok" if age <= warn_hours else "warning" if age <= stale_hours else "stale"
    return {"name": name, "status": status, "generated_at": generated_at, "age_hours": age, "message": "Актуально" if status == "ok" else "Требуется обновление"}


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _check_http_sync(url: str) -> dict[str, Any]:
    if not url:
        return {"status": "missing", "message": "BROWSER_BASE_URL не настроен"}
    request = Request(url, method="HEAD", headers={"User-Agent": "AI-BIT-System-Health/1.0"})
    try:
        with urlopen(request, timeout=15) as response:
            return {"status": "ok", "http_status": response.status, "message": "Портал доступен"}
    except HTTPError as exc:
        return {"status": "warning" if exc.code < 500 else "error", "http_status": exc.code, "message": f"HTTP {exc.code}"}
    except (URLError, TimeoutError) as exc:
        return {"status": "error", "message": str(exc)}


async def build_system_health(artifacts_dir: Path, crawl_history: Any, browser_base_url: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    browser_check = await asyncio.to_thread(_check_http_sync, browser_base_url)
    checks.append({"key": "browser", "name": "Bitrix24 / Browser", **browser_check})

    webhook = os.getenv("BITRIX_WEBHOOK_URL", "").strip()
    if not webhook:
        checks.append({"key": "rest", "name": "Bitrix REST", "status": "missing", "message": "BITRIX_WEBHOOK_URL не настроен"})
    else:
        try:
            current = await rest_call(webhook, "user.current", {})
            user = current.get("result") or {}
            checks.append({"key": "rest", "name": "Bitrix REST", "status": "ok", "message": "Webhook работает", "user_id": user.get("ID")})
        except RuntimeError as exc:
            checks.append({"key": "rest", "name": "Bitrix REST", "status": "error", "message": str(exc)[:500]})

    ai = ai_status()
    checks.append({"key": "ai", "name": "Groq / AI", "status": "ok" if ai.get("configured") else "missing", "message": "AI настроен" if ai.get("configured") else "AI key не настроен", "provider": ai.get("provider"), "model": ai.get("model")})

    crawl = None
    try:
        crawl = crawl_history.latest()
    except FileNotFoundError:
        pass
    operations = _read_json(artifacts_dir / "operations" / "latest.json")
    architecture = _read_json(artifacts_dir / "business-architecture" / "latest.json")
    process_mining = _read_json(artifacts_dir / "process-mining" / "latest.json")

    freshness = [
        _freshness("Crawl", (crawl or {}).get("generated_at") or (crawl or {}).get("started_at"), warn_hours=168, stale_hours=336),
        _freshness("Operational snapshot", (operations or {}).get("generated_at"), warn_hours=24, stale_hours=48),
        _freshness("Business Architecture", (architecture or {}).get("generated_at"), warn_hours=168, stale_hours=336),
        _freshness("Process Mining", (process_mining or {}).get("generated_at"), warn_hours=168, stale_hours=336),
    ]

    rights: list[dict[str, Any]] = []
    for domain_name, domain in (architecture or {}).get("domains", {}).items():
        for source in domain.get("sources", []):
            rights.append({
                "domain": domain_name,
                "method": source.get("method") or source.get("source") or "unknown",
                "status": "ok" if source.get("ok") else "denied",
                "error": source.get("error"),
            })

    data_quality = {
        "crawl_pages": len((crawl or {}).get("nodes", [])),
        "active_users": (operations or {}).get("summary", {}).get("active_users"),
        "tasks_loaded": (operations or {}).get("summary", {}).get("tasks_loaded"),
        "enterprise_health": (architecture or {}).get("enterprise_health"),
        "architecture_evidence": {key: value.get("evidence_status") for key, value in (architecture or {}).get("domains", {}).items()},
    }

    statuses = [item["status"] for item in checks] + [item["status"] for item in freshness]
    overall = "error" if "error" in statuses else "warning" if any(x in statuses for x in ("warning", "stale", "missing")) else "ok"
    denied = sum(1 for item in rights if item["status"] == "denied")

    recommendations: list[dict[str, str]] = []
    for item in freshness:
        if item["status"] in {"stale", "missing"}:
            recommendations.append({"severity": "high", "title": f"Обновить {item['name']}", "action": "Запустить соответствующий сбор данных из единой админки."})
        elif item["status"] == "warning":
            recommendations.append({"severity": "medium", "title": f"Скоро устареет: {item['name']}", "action": "Запланировать обновление данных."})
    if denied:
        recommendations.append({"severity": "high", "title": "Недостаточно прав webhook", "action": f"Проверить {denied} недоступных REST-источников в разделе прав."})

    return {
        "version": "1.0.0-rc.3",
        "generated_at": _now().isoformat(),
        "overall_status": overall,
        "summary": {
            "services_ok": sum(1 for item in checks if item["status"] == "ok"),
            "services_total": len(checks),
            "fresh_datasets": sum(1 for item in freshness if item["status"] == "ok"),
            "datasets_total": len(freshness),
            "denied_sources": denied,
        },
        "checks": checks,
        "freshness": freshness,
        "rights": rights,
        "data_quality": data_quality,
        "recommendations": recommendations,
    }
