from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PLATFORM_CORE_URL = os.getenv("PLATFORM_CORE_URL", "http://platform-core:8070").rstrip("/")
PLATFORM_CORE_TIMEOUT_SECONDS = float(os.getenv("PLATFORM_CORE_TIMEOUT_SECONDS", "10"))


def _post_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    endpoint = f"{PLATFORM_CORE_URL}/api/v1/browser/evidence"
    payload = dict(evidence)
    payload.pop("platform_delivery", None)
    payload.setdefault("source", "browser-worker")
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=PLATFORM_CORE_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
            return {
                "status": "delivered",
                "http_status": response.status,
                "endpoint": endpoint,
                "receipt": body,
            }
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        return {
            "status": "failed",
            "http_status": exc.code,
            "endpoint": endpoint,
            "error": detail,
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "status": "failed",
            "http_status": None,
            "endpoint": endpoint,
            "error": f"{type(exc).__name__}: {exc}",
        }


async def publish_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(_post_evidence, evidence)
