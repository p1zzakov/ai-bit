from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VERSION = "3.6.1"
PROTOCOL_VERSION = "2025-03-26"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json_env(name: str, default: Any) -> Any:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> tuple[int, Any, int]:
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request_headers = {"Accept": "application/json, text/event-stream", **(headers or {})}
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
                data = {"raw": raw[:20000]}
            return response.status, data, elapsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        elapsed = int((time.monotonic() - started) * 1000)
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw[:20000]}
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


class StdioMcpClient:
    def __init__(self, command: str, args: list[str], env: dict[str, str], timeout: float) -> None:
        self.command = command
        self.args = args
        self.env = {**os.environ, **env}
        self.timeout = timeout
        self.process: subprocess.Popen[str] | None = None
        self._next_id = 1
        self._lock = threading.Lock()

    def __enter__(self) -> "StdioMcpClient":
        self.process = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=self.env,
        )
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self.process is None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=3)
        except Exception:
            self.process.kill()

    def _write(self, payload: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("MCP process is not running")
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})
            if self.process is None or self.process.stdout is None:
                raise RuntimeError("MCP stdout is not available")
            deadline = time.monotonic() + self.timeout
            while time.monotonic() < deadline:
                line = self.process.stdout.readline()
                if not line:
                    code = self.process.poll()
                    stderr = ""
                    if self.process.stderr is not None:
                        stderr = self.process.stderr.read()[-4000:]
                    raise RuntimeError(f"MCP process stopped, code={code}, stderr={stderr}")
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if message.get("id") == request_id:
                    return message
            raise TimeoutError(f"MCP request timed out: {method}")

    def initialize(self) -> dict[str, Any]:
        response = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "AI-BIT Enterprise", "version": VERSION},
            },
        )
        if response.get("error"):
            raise RuntimeError(str(response["error"]))
        self.notify("notifications/initialized")
        return response.get("result") or {}


class HttpMcpClient:
    def __init__(self, url: str, headers: dict[str, str], timeout: float) -> None:
        self.url = url
        self.headers = headers
        self.timeout = timeout
        self._next_id = 1

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        status, data, _ = _request_json(
            self.url,
            method="POST",
            headers=self.headers,
            body={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}},
            timeout=self.timeout,
        )
        if not 200 <= status < 300:
            raise RuntimeError(f"MCP HTTP {status}: {data}")
        if not isinstance(data, dict):
            raise RuntimeError("MCP response is not a JSON object")
        return data

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        _request_json(
            self.url,
            method="POST",
            headers=self.headers,
            body={"jsonrpc": "2.0", "method": method, "params": params or {}},
            timeout=self.timeout,
        )

    def initialize(self) -> dict[str, Any]:
        response = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "AI-BIT Enterprise", "version": VERSION},
            },
        )
        if response.get("error"):
            raise RuntimeError(str(response["error"]))
        self.notify("notifications/initialized")
        return response.get("result") or {}


class McpProvider(SourceProvider):
    source_type = "mcp"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.provider_id = str(config.get("id") or "mcp").strip()
        self.name = str(config.get("name") or self.provider_id)
        self.transport = str(config.get("transport") or "stdio").lower()
        self.timeout = float(config.get("timeout_seconds") or 30)
        self.allowed_tools = {str(x) for x in config.get("allowed_tools", []) if str(x).strip()}
        calls = config.get("calls") if isinstance(config.get("calls"), list) else []
        self.calls = [row for row in calls if isinstance(row, dict)]

    def status(self) -> dict[str, Any]:
        configured = False
        endpoint = ""
        if self.transport == "stdio":
            endpoint = str(self.config.get("command") or "")
            configured = bool(endpoint)
        elif self.transport in {"http", "streamable_http"}:
            endpoint = str(self.config.get("url") or "")
            configured = bool(endpoint)
        return {
            "id": self.provider_id,
            "name": self.name,
            "type": self.source_type,
            "transport": self.transport,
            "configured": configured,
            "endpoint": endpoint,
            "read_only": True,
            "allowed_tools": sorted(self.allowed_tools),
            "planned_calls": [str(row.get("name") or "") for row in self.calls],
        }

    def _client(self) -> Any:
        if self.transport == "stdio":
            command = str(self.config.get("command") or "")
            args = [str(x) for x in self.config.get("args", [])]
            env = {str(k): str(v) for k, v in (self.config.get("env") or {}).items()}
            return StdioMcpClient(command, args, env, self.timeout)
        if self.transport in {"http", "streamable_http"}:
            headers = {str(k): str(v) for k, v in (self.config.get("headers") or {}).items()}
            token = str(self.config.get("bearer_token") or "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
            return HttpMcpClient(str(self.config.get("url") or ""), headers, self.timeout)
        raise ValueError(f"Unsupported MCP transport: {self.transport}")

    def _collect_with_client(self, client: Any) -> dict[str, Any]:
        server = client.initialize()
        tools_response = client.request("tools/list")
        if tools_response.get("error"):
            raise RuntimeError(str(tools_response["error"]))
        tools = (tools_response.get("result") or {}).get("tools") or []
        discovered = {
            str(row.get("name") or ""): row
            for row in tools
            if isinstance(row, dict) and row.get("name")
        }
        calls_result: dict[str, Any] = {}
        errors: list[dict[str, Any]] = []
        for row in self.calls:
            name = str(row.get("name") or "").strip()
            arguments = row.get("arguments") if isinstance(row.get("arguments"), dict) else {}
            if not name:
                continue
            if name not in self.allowed_tools:
                errors.append({"tool": name, "error": "blocked_by_explicit_allowlist"})
                continue
            if name not in discovered:
                errors.append({"tool": name, "error": "tool_not_advertised_by_server"})
                continue
            started = time.monotonic()
            response = client.request("tools/call", {"name": name, "arguments": arguments})
            elapsed = int((time.monotonic() - started) * 1000)
            calls_result[name] = {
                "success": not bool(response.get("error")),
                "duration_ms": elapsed,
                "result": response.get("result"),
                "error": response.get("error"),
            }
            if response.get("error"):
                errors.append({"tool": name, "error": response.get("error")})
        return {
            "server": server,
            "discovered_tools": list(discovered.values()),
            "calls": calls_result,
            "errors": errors,
        }

    def collect(self) -> dict[str, Any]:
        result = {**self.status(), "collected_at": _now(), "server": {}, "discovered_tools": [], "calls": {}, "errors": []}
        if not result["configured"]:
            result["status"] = "not_configured"
            return result
        try:
            client = self._client()
            if isinstance(client, StdioMcpClient):
                with client:
                    payload = self._collect_with_client(client)
            else:
                payload = self._collect_with_client(client)
            result.update(payload)
            result["status"] = "ok" if not result["errors"] else "partial"
        except Exception as exc:
            result["status"] = "error"
            result["errors"] = [{"error": str(exc)}]
        return result


class GenericHttpProvider(SourceProvider):
    source_type = "http_read_only"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.provider_id = str(config.get("id") or "http")

    def status(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": str(self.config.get("name") or self.provider_id),
            "type": self.source_type,
            "configured": bool(self.config.get("base_url")),
            "endpoint": str(self.config.get("base_url") or ""),
            "read_only": True,
        }

    def collect(self) -> dict[str, Any]:
        result = {**self.status(), "collected_at": _now(), "objects": {}, "errors": []}
        if not result["configured"]:
            result["status"] = "not_configured"
            return result
        base_url = str(self.config.get("base_url") or "").rstrip("/")
        timeout = float(self.config.get("timeout_seconds") or 20)
        headers = {str(k): str(v) for k, v in (self.config.get("headers") or {}).items()}
        endpoints = self.config.get("endpoints") if isinstance(self.config.get("endpoints"), dict) else {}
        for name, path in endpoints.items():
            url = base_url + "/" + str(path).lstrip("/")
            try:
                status, data, elapsed = _request_json(url, headers=headers, timeout=timeout)
                result["objects"][str(name)] = {
                    "url": url,
                    "http_status": status,
                    "duration_ms": elapsed,
                    "success": 200 <= status < 300,
                    "data": data,
                }
                if not 200 <= status < 300:
                    result["errors"].append({"endpoint": name, "http_status": status})
            except Exception as exc:
                result["errors"].append({"endpoint": name, "error": str(exc)})
        result["status"] = "ok" if not result["errors"] else "partial"
        return result


def _legacy_mcp_1c() -> list[dict[str, Any]]:
    command = os.getenv("ONEC_MCP_COMMAND", "").strip()
    if not command:
        return []
    return [
        {
            "id": "mcp_1c",
            "name": "1C MCP",
            "transport": "stdio",
            "command": command,
            "args": _json_env("ONEC_MCP_ARGS_JSON", []),
            "env": _json_env("ONEC_MCP_ENV_JSON", {}),
            "timeout_seconds": float(os.getenv("ONEC_MCP_TIMEOUT_SECONDS", "30")),
            "allowed_tools": _json_env("ONEC_MCP_ALLOWED_TOOLS_JSON", []),
            "calls": _json_env("ONEC_MCP_CALLS_JSON", []),
        }
    ]


def providers() -> list[SourceProvider]:
    mcp_configs = _json_env("MCP_SERVERS_JSON", [])
    http_configs = _json_env("HTTP_SOURCES_JSON", [])
    if not isinstance(mcp_configs, list):
        mcp_configs = []
    if not isinstance(http_configs, list):
        http_configs = []
    if not mcp_configs:
        mcp_configs = _legacy_mcp_1c()
    rows: list[SourceProvider] = []
    rows.extend(McpProvider(row) for row in mcp_configs if isinstance(row, dict))
    rows.extend(GenericHttpProvider(row) for row in http_configs if isinstance(row, dict))
    return rows


def external_sources_status() -> dict[str, Any]:
    rows = [provider.status() for provider in providers()]
    return {
        "version": VERSION,
        "mode": "read_only",
        "generated_at": _now(),
        "providers": rows,
        "summary": {"total": len(rows), "configured": sum(1 for row in rows if row.get("configured"))},
        "execution_policy": {
            "mcp_tool_discovery": True,
            "mcp_explicit_allowlist_required": True,
            "mcp_write_tools_allowed": False,
            "http_methods": ["GET"],
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
            "error": sum(1 for row in rows if row.get("status") == "error"),
        },
        "execution_policy": external_sources_status()["execution_policy"],
    }
    folder = artifacts_dir / "external-sources"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def latest_external_sources(artifacts_dir: Path) -> dict[str, Any]:
    path = artifacts_dir / "external-sources" / "latest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else external_sources_status()
    except (OSError, json.JSONDecodeError, TypeError):
        return external_sources_status()
