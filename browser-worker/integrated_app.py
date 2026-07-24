from __future__ import annotations

import json
from typing import Any

from fastapi import Request
from fastapi.responses import Response

from app import app
from platform_client import publish_evidence

SCAN_PATHS = {"/scan", "/scan/all", "/scan/batch"}


def _is_scan_path(path: str) -> bool:
    return path in SCAN_PATHS or path.startswith("/scan/preset/")


def _evidence_items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    results = payload.get("results")
    if isinstance(results, list):
        return [item for item in results if isinstance(item, dict)]
    if {"generated_at", "name", "url"}.issubset(payload):
        return [payload]
    return []


@app.middleware("http")
async def deliver_scan_evidence(request: Request, call_next):
    response = await call_next(request)
    if request.method != "POST" or not _is_scan_path(request.url.path):
        return response

    body = b"".join([chunk async for chunk in response.body_iterator])
    headers = dict(response.headers)
    headers.pop("content-length", None)

    if response.status_code < 400:
        try:
            payload = json.loads(body.decode("utf-8"))
            items = _evidence_items(payload)
            for evidence in items:
                evidence["platform_delivery"] = await publish_evidence(evidence)
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

    return Response(
        content=body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type,
        background=response.background,
    )
