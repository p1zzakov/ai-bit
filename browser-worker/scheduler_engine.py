from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


JOB_DEFINITIONS = {
    "operations": {
        "title": "Operational snapshot",
        "method": "POST",
        "path": "/operations/collect",
        "default_schedule": "daily@06:00",
    },
    "business_architecture": {
        "title": "Business Architecture Audit",
        "method": "POST",
        "path": "/business-architecture/collect",
        "default_schedule": "weekly:mon@07:00",
    },
    "crawl": {
        "title": "Portal crawl",
        "method": "POST",
        "path": "/crawl",
        "default_schedule": "weekly:sun@03:00",
        "body": {
            "start_path": "/",
            "max_pages": 150,
            "max_depth": 3,
            "include_query": False,
            "save_html": False,
            "delay_ms": 300,
        },
    },
    "executive_report": {
        "title": "Executive report",
        "method": "POST",
        "path": "/reports/generate",
        "default_schedule": "monthly:1@08:00",
    },
}

DAY_NAMES = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "y"}


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _schedule_env_name(job: str) -> str:
    return f"SCHEDULER_{job.upper()}_SCHEDULE"


def _enabled_env_name(job: str) -> str:
    return f"SCHEDULER_{job.upper()}_ENABLED"


def parse_schedule(value: str) -> dict[str, Any]:
    raw = value.strip().lower()
    if raw.startswith("daily@"):
        hour, minute = map(int, raw.split("@", 1)[1].split(":"))
        return {"kind": "daily", "hour": hour, "minute": minute}
    if raw.startswith("weekly:"):
        day, clock = raw.split(":", 1)[1].split("@", 1)
        hour, minute = map(int, clock.split(":"))
        if day not in DAY_NAMES:
            raise ValueError(f"Unknown weekday: {day}")
        return {"kind": "weekly", "weekday": DAY_NAMES[day], "hour": hour, "minute": minute}
    if raw.startswith("monthly:"):
        day, clock = raw.split(":", 1)[1].split("@", 1)
        hour, minute = map(int, clock.split(":"))
        return {"kind": "monthly", "day": int(day), "hour": hour, "minute": minute}
    raise ValueError("Schedule must be daily@HH:MM, weekly:mon@HH:MM or monthly:DAY@HH:MM")


def is_due(schedule: dict[str, Any], now: datetime) -> bool:
    if now.hour != schedule["hour"] or now.minute != schedule["minute"]:
        return False
    if schedule["kind"] == "daily":
        return True
    if schedule["kind"] == "weekly":
        return now.weekday() == schedule["weekday"]
    if schedule["kind"] == "monthly":
        return now.day == schedule["day"]
    return False


class SchedulerService:
    def __init__(self, artifacts_dir: Path, base_url: str = "http://127.0.0.1:8090") -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.root = self.artifacts_dir / "scheduler"
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self.history_path = self.root / "history.jsonl"
        self.base_url = base_url.rstrip("/")
        self.enabled = _bool_env("SCHEDULER_ENABLED", True)
        self.timezone_name = os.getenv("SCHEDULER_TIMEZONE", "Asia/Almaty")
        try:
            self.timezone = ZoneInfo(self.timezone_name)
        except Exception:
            self.timezone_name = "UTC"
            self.timezone = ZoneInfo("UTC")
        self.poll_seconds = max(20, int(os.getenv("SCHEDULER_POLL_SECONDS", "30")))
        self._loop_task: asyncio.Task[None] | None = None
        self._locks = {name: asyncio.Lock() for name in JOB_DEFINITIONS}
        self._state: dict[str, Any] = _read_json(self.state_path, {"jobs": {}})
        self._state.setdefault("jobs", {})

    def jobs(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for name, definition in JOB_DEFINITIONS.items():
            schedule_raw = os.getenv(_schedule_env_name(name), definition["default_schedule"])
            enabled = _bool_env(_enabled_env_name(name), True)
            try:
                parsed = parse_schedule(schedule_raw)
                schedule_error = None
            except ValueError as exc:
                parsed = None
                schedule_error = str(exc)
            state = self._state["jobs"].get(name, {})
            rows.append({
                "name": name,
                "title": definition["title"],
                "enabled": enabled,
                "schedule": schedule_raw,
                "schedule_valid": parsed is not None,
                "schedule_error": schedule_error,
                "running": self._locks[name].locked(),
                "last_run_at": state.get("last_run_at"),
                "last_status": state.get("last_status"),
                "last_duration_seconds": state.get("last_duration_seconds"),
                "last_error": state.get("last_error"),
                "last_trigger": state.get("last_trigger"),
            })
        return rows

    def status(self) -> dict[str, Any]:
        rows = self.jobs()
        return {
            "version": "1.0.0-rc.6",
            "enabled": self.enabled,
            "timezone": self.timezone_name,
            "poll_seconds": self.poll_seconds,
            "running_jobs": sum(1 for row in rows if row["running"]),
            "failed_jobs": sum(1 for row in rows if row.get("last_status") == "error"),
            "jobs": rows,
            "history": self.history(limit=30),
        }

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        try:
            lines = self.history_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        rows: list[dict[str, Any]] = []
        for line in reversed(lines[-max(limit, 1):]):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    async def start(self) -> None:
        if not self.enabled or self._loop_task is not None:
            return
        self._loop_task = asyncio.create_task(self._loop(), name="ai-bit-scheduler")

    async def stop(self) -> None:
        if self._loop_task is None:
            return
        self._loop_task.cancel()
        try:
            await self._loop_task
        except asyncio.CancelledError:
            pass
        self._loop_task = None

    async def _loop(self) -> None:
        while True:
            await self._tick()
            await asyncio.sleep(self.poll_seconds)

    async def _tick(self) -> None:
        now = datetime.now(self.timezone)
        minute_key = now.strftime("%Y-%m-%dT%H:%M")
        for row in self.jobs():
            if not row["enabled"] or not row["schedule_valid"] or row["running"]:
                continue
            parsed = parse_schedule(row["schedule"])
            if not is_due(parsed, now):
                continue
            state = self._state["jobs"].get(row["name"], {})
            if state.get("last_schedule_key") == minute_key:
                continue
            state["last_schedule_key"] = minute_key
            self._state["jobs"][row["name"]] = state
            self._save_state()
            asyncio.create_task(self.run(row["name"], trigger="schedule"))

    async def run(self, name: str, trigger: str = "manual") -> dict[str, Any]:
        if name not in JOB_DEFINITIONS:
            raise KeyError(name)
        lock = self._locks[name]
        if lock.locked():
            raise RuntimeError(f"Job {name} is already running")
        async with lock:
            started = datetime.now(UTC)
            record: dict[str, Any] = {
                "job": name,
                "title": JOB_DEFINITIONS[name]["title"],
                "trigger": trigger,
                "started_at": started.isoformat(),
                "status": "running",
            }
            try:
                response = await asyncio.to_thread(self._request, name)
                record["status"] = "ok"
                record["result"] = response
                error = None
            except Exception as exc:
                record["status"] = "error"
                record["error"] = str(exc)
                error = exc
            finished = datetime.now(UTC)
            record["finished_at"] = finished.isoformat()
            record["duration_seconds"] = round((finished - started).total_seconds(), 3)
            state = self._state["jobs"].setdefault(name, {})
            state.update({
                "last_run_at": record["finished_at"],
                "last_status": record["status"],
                "last_duration_seconds": record["duration_seconds"],
                "last_error": record.get("error"),
                "last_trigger": trigger,
            })
            self._save_state()
            self._append_history(record)
            if error is not None:
                raise RuntimeError(str(error)) from error
            return record

    def _request(self, name: str) -> dict[str, Any]:
        definition = JOB_DEFINITIONS[name]
        body = definition.get("body")
        data = json.dumps(body).encode("utf-8") if body is not None else b""
        request = urllib.request.Request(
            self.base_url + definition["path"],
            data=data,
            method=definition["method"],
            headers={"Content-Type": "application/json", "User-Agent": "AI-BIT-Scheduler/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {raw[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"response": raw[:2000]}
        return {
            "endpoint": definition["path"],
            "summary": payload.get("summary") if isinstance(payload, dict) else None,
            "id": payload.get("id") if isinstance(payload, dict) else None,
            "history_id": payload.get("history_id") if isinstance(payload, dict) else None,
        }

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_history(self, record: dict[str, Any]) -> None:
        with self.history_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
