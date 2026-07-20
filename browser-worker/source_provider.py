from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "3.6.0"
WRITE_MARKERS = (
    "add", "create", "update", "delete", "remove", "write", "post", "put",
    "patch", "set", "execute", "run", "start", "stop", "change", "import",
)


def _json_env(name: str, default: Any) -> Any:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_tool(name: str) -> bool:
    value = name.lower().replace("-", "_")
    return not any(marker in value for marker in WRITE_MARKERS)


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 20.0,
) -> tuple[int, Any, int]:
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=payload, headers=request_headers, method=method)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            elapsed = int((time.monotonic() - started) * 1000)
            try:
                data: Any = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {"raw": raw[:10000]}
            return response.status, data, elapsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        elapsed = int((time.monotonic() - started) * 1000)
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw[:10000]}
        return exc.code, data, elapsed


class SourceProvider(ABC):
    provider_id: str
    source_type: str

    @abstractmethod
    def status(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        raise NotImplementedError


class OneCHttpProvider(SourceProvider):
    provider_id = "onec_http"
    source_type = "1c_http"

    def __init__(self) -> None:
        self.base_url = os.getenv("ONEC_HTTP_BASE_URL", "").rstrip("/")
        self.timeout = float(os.getenv("ONEC_HTTP_TIMEOUT_SECONDS", "20"))
        self.endpoints = _json_env(
            "ONEC_HTTP_ENDPOINTS_JSON",
            {
                "metadata": "/api/metadata",
                "catalogs": "/api/catalogs",
                "documents": "/api/documents",
                "integration": "/api/integration/status",
            },
        )
        self.headers: dict[str, str] = {}
        token = os.getenv("ONEC_HTTP_BEARER_TOKEN", "").strip()
        username = os.getenv("ONEC_HTTP_USERNAME", "").strip()
        password = os.getenv("ONEC_HTTP_PASSWORD", "")
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        elif username:
            encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
            self.headers["Authorization"] = f"Basic {encoded}"

    def status(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "type": self.source_type,
            "configured": bool(self.base_url),
            "base_url": self.base_url,
            "read_only": True,
            "endpoints": list(self.endpoints) if isinstance(self.endpoints, dict) else [],
        }

    def collect(self) -> dict[str, Any]:
        result = {**self.status(), "collected_at": _now(), "objects": {}, "errors": []}
        if not self.base_url:
            result["status"] = "not_configured"
            return result
        endpoints = self.endpoints if isinstance(self.endpoints, dict) else {}
        for name, path in endpoints.items():
            target = urllib.parse.urljoin(self.base_url + "/", str(path).lstrip("/"))
            try:
                status, data, elapsed = _request_json(
                    target, headers=self.headers, timeout=self.timeout
                )
                result["objects"][str(name)] = {
                    "url": target,
                    "http_status": status,
                    "duration_ms": elapsed,
                    "success": 200 <= status < 300,
                    "data": data,
                }
                if not 200 <= status < 300:
                    result["errors"].append({"endpoint": name, "http_status": status})
            except Exception as exc:  # source failure must not break the platform
                result["errors"].append({"endpoint": name, "error": str(exc)})
        result["status"] = "ok" if not result["errors"] else "partial"
        return result


class OneCMcpProvider(SourceProvider):
    provider_id = "onec_mcp"
    source_type = "mcp_http"

    def __init__(self) -> None:
        self.url = os.getenv("ONEC_MCP_URL", "").strip()
        self.timeout = float(os.getenv("ONEC_MCP_TIMEOUT_SECONDS", "30"))
        self.token = os.getenv("ONEC_MCP_BEARER_TOKEN", "").strip()
        configured_tools = _json_env("ONEC_MCP_READ_TOOLS_JSON", [])
        self.tools = [row for row in configured_tools if isinstance(row, dict)]

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def status(self) -> dict[str, Any]:
        tools = [str(row.get("name") or "") for row in self.tools]
        return {
            "id": self.provider_id,
            "type": self.source_type,
            "configured": bool(self.url),
            "url": self.url,
            "read_only": True,
            "configured_tools": tools,
            "blocked_tools": [name for name in tools if not _safe_tool(name)],
        }

    def collect(self) -> dict[str, Any]:
        result = {**self.status(), "collected_at": _now(), "tools": {}, "errors": []}
        if not self.url:
            result["status"] = "not_configured"
            return result
        for index, tool in enumerate(self.tools, start=1):
            name = str(tool.get("name") or "").strip()
            arguments = tool.get("arguments") if isinstance(tool.get("arguments"), dict) else {}
            if not name:
                continue
            if not _safe_tool(name):
                result["errors"].append({"tool": name, "error": "blocked_by_read_only_policy"})
                continue
            body = {
                "jsonrpc": "2.0",
                "id": index,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
            try:
                status, data, elapsed = _request_json(
                    self.url,
                    method="POST",
                    headers=self.headers,
                    body=body,
                    timeout=self.timeout,
                )
                rpc_error = data.get("error") if isinstance(data, dict) else None
                result["tools"][name] = {
                    "http_status": status,
                    "duration_ms": elapsed,
                    "success": 200 <= status < 300 and not rpc_error,
                    "result": data.get("result") if isinstance(data, dict) else data,
                    "error": rpc_error,
                }
                if not 200 <= status < 300 or rpc_error:
                    result["errors"].append({"tool": name, "http_status": status, "error": rpc_error})
            except Exception as exc:
                result["errors"].append({"tool": name, "error": str(exc)})
        result["status"] = "ok" if not result["errors"] else "partial"
        return result


def providers() -> list[SourceProvider]:
    return [OneCHttpProvider(), OneCMcpProvider()]


def external_sources_status() -> dict[str, Any]:
    rows = [provider.status() for provider in providers()]
    return {
        "version": VERSION,
        "mode": "read_only",
        "generated_at": _now(),
        "providers": rows,
        "summary": {
            "total": len(rows),
            "configured": sum(1 for row in rows if row.get("configured")),
        },
        "execution_policy": {
            "http_methods": ["GET"],
            "mcp_transport_post_allowed": True,
            "mcp_write_tools_allowed": False,
            "automatic_changes": False,
        },
    }


def collect_external_sources(artifacts_dir: Path) -> dict[str, Any]:
    rows = [provider.collect() for provider in providers()]
    payload = {
        "version": VERSION,
        "mode": "read_only",
        "generated_at": _now(),
        "providers": rows,
        "summary": {
            "total": len(rows),
            "configured": sum(1 for row in rows if row.get("configured")),
            "ok": sum(1 for row in rows if row.get("status") == "ok"),
            "partial": sum(1 for row in rows if row.get("status") == "partial"),
        },
        "execution_policy": external_sources_status()["execution_policy"],
    }
    folder = artifacts_dir / "external-sources"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def latest_external_sources(artifacts_dir: Path) -> dict[str, Any]:
    path = artifacts_dir / "external-sources" / "latest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else external_sources_status()
    except (OSError, json.JSONDecodeError, TypeError):
        return external_sources_status()
