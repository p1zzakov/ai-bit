from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def list_operational_snapshots(artifacts_dir: Path, limit: int = 500) -> list[dict[str, Any]]:
    root = artifacts_dir / "operations"
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("operations-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        generated = _parse_dt(data.get("generated_at"))
        if generated is None:
            continue
        rows.append({
            "id": path.stem,
            "generated_at": generated.isoformat(),
            "path": str(path),
            "summary": data.get("summary", {}),
            "data": data,
        })
    rows.sort(key=lambda x: x["generated_at"], reverse=True)
    return rows[:limit]


def _delta(current: Any, baseline: Any) -> float:
    try:
        return round(float(current or 0) - float(baseline or 0), 1)
    except (TypeError, ValueError):
        return 0.0


def _index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in items if item.get("id") is not None}


def _risk_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(str(value), 0)


def _compare_entities(current: list[dict[str, Any]], baseline: list[dict[str, Any]], *, kind: str) -> dict[str, list[dict[str, Any]]]:
    before = _index(baseline)
    after = _index(current)
    improved: list[dict[str, Any]] = []
    worsened: list[dict[str, Any]] = []
    entered_risk: list[dict[str, Any]] = []
    exited_risk: list[dict[str, Any]] = []

    for entity_id, now in after.items():
        old = before.get(entity_id)
        if not old:
            continue
        now_risk = str(now.get("risk", "low"))
        old_risk = str(old.get("risk", "low"))
        row = {
            "id": entity_id,
            "name": now.get("name") or entity_id,
            "risk_before": old_risk,
            "risk_after": now_risk,
            "open_delta": _delta(now.get("open_tasks" if kind == "employee" else "open"), old.get("open_tasks" if kind == "employee" else "open")),
            "overdue_delta": _delta(now.get("overdue_tasks" if kind == "employee" else "overdue"), old.get("overdue_tasks" if kind == "employee" else "overdue")),
            "overdue_rate_delta": _delta(now.get("overdue_rate"), old.get("overdue_rate")),
            "without_deadline_delta": _delta(now.get("without_deadline"), old.get("without_deadline")),
        }
        if _risk_rank(now_risk) > _risk_rank(old_risk) or row["overdue_rate_delta"] >= 10:
            worsened.append(row)
        elif _risk_rank(now_risk) < _risk_rank(old_risk) or row["overdue_rate_delta"] <= -10:
            improved.append(row)
        if old_risk not in {"high", "critical"} and now_risk in {"high", "critical"}:
            entered_risk.append(row)
        if old_risk in {"high", "critical"} and now_risk not in {"high", "critical"}:
            exited_risk.append(row)

    worsened.sort(key=lambda x: (x["overdue_rate_delta"], x["overdue_delta"]), reverse=True)
    improved.sort(key=lambda x: (x["overdue_rate_delta"], x["overdue_delta"]))
    return {
        "improved": improved[:25],
        "worsened": worsened[:25],
        "entered_risk": entered_risk[:25],
        "exited_risk": exited_risk[:25],
    }


def _insufficient_result(*, days: int, snapshots: list[dict[str, Any]], current_meta: dict[str, Any], series: list[dict[str, Any]], message: str, baseline_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    current_dt = _parse_dt(current_meta.get("generated_at"))
    baseline_dt = _parse_dt((baseline_meta or {}).get("generated_at"))
    actual_days = (current_dt - baseline_dt).days if current_dt and baseline_dt else None
    return {
        "version": "1.0.0-beta.1",
        "period_days": days,
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "insufficient_history",
        "direction": "unknown",
        "available_snapshots": len(snapshots),
        "actual_comparison_days": actual_days,
        "current_snapshot": current_meta.get("id"),
        "baseline_snapshot": (baseline_meta or {}).get("id"),
        "current_generated_at": current_meta.get("generated_at"),
        "baseline_generated_at": (baseline_meta or {}).get("generated_at"),
        "current": current_meta.get("summary", {}),
        "baseline": (baseline_meta or {}).get("summary") if baseline_meta else None,
        "deltas": {},
        "employees": {"improved": [], "worsened": [], "entered_risk": [], "exited_risk": []},
        "departments": {"improved": [], "worsened": [], "entered_risk": [], "exited_risk": []},
        "series": series,
        "message": message,
    }


def build_operational_trends(artifacts_dir: Path, days: int = 30) -> dict[str, Any]:
    if days not in {7, 30, 90}:
        raise ValueError("days must be one of 7, 30 or 90")
    snapshots = list_operational_snapshots(artifacts_dir)
    if not snapshots:
        raise FileNotFoundError("No operational snapshots")

    current_meta = snapshots[0]
    current = current_meta["data"]
    current_dt = _parse_dt(current_meta["generated_at"]) or datetime.now(UTC)
    target = current_dt - timedelta(days=days)
    baseline_meta = None
    for item in snapshots[1:]:
        item_dt = _parse_dt(item["generated_at"])
        if item_dt and item_dt <= target:
            baseline_meta = item
            break
    if baseline_meta is None and len(snapshots) > 1:
        baseline_meta = snapshots[-1]

    series = [
        {
            "generated_at": item["generated_at"],
            "open": item["summary"].get("open", 0),
            "overdue": item["summary"].get("overdue", 0),
            "overdue_rate": item["summary"].get("overdue_rate", 0),
            "without_deadline": item["summary"].get("without_deadline", 0),
            "completed": item["summary"].get("completed", 0),
            "employees_at_risk": item["summary"].get("employees_at_risk", 0),
        }
        for item in reversed(snapshots)
        if (_parse_dt(item["generated_at"]) or current_dt) >= current_dt - timedelta(days=days)
    ]

    if baseline_meta is None:
        return _insufficient_result(
            days=days,
            snapshots=snapshots,
            current_meta=current_meta,
            series=series,
            message="Для расчёта динамики требуется минимум два operational snapshot.",
        )

    baseline_dt = _parse_dt(baseline_meta["generated_at"])
    actual_seconds = max(0, int((current_dt - baseline_dt).total_seconds())) if baseline_dt else 0
    actual_days = actual_seconds // 86400
    if actual_days < 1:
        return _insufficient_result(
            days=days,
            snapshots=snapshots,
            current_meta=current_meta,
            baseline_meta=baseline_meta,
            series=series,
            message="Snapshot собраны в течение одного дня. Реальная динамика появится после следующего дневного среза.",
        )

    baseline = baseline_meta["data"]
    current_summary = current.get("summary", {})
    baseline_summary = baseline.get("summary", {})
    fields = ["open", "overdue", "overdue_rate", "without_deadline", "completed", "employees_at_risk"]
    deltas = {field: _delta(current_summary.get(field), baseline_summary.get(field)) for field in fields}

    direction = "stable"
    if deltas["overdue_rate"] <= -5 and deltas["employees_at_risk"] <= 0:
        direction = "improving"
    elif deltas["overdue_rate"] >= 5 or deltas["employees_at_risk"] > 0:
        direction = "worsening"

    return {
        "version": "1.0.0-beta.1",
        "period_days": days,
        "actual_comparison_days": actual_days,
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "ok",
        "direction": direction,
        "available_snapshots": len(snapshots),
        "current_snapshot": current_meta["id"],
        "baseline_snapshot": baseline_meta["id"],
        "current_generated_at": current_meta["generated_at"],
        "baseline_generated_at": baseline_meta["generated_at"],
        "current": current_summary,
        "baseline": baseline_summary,
        "deltas": deltas,
        "employees": _compare_entities(current.get("employees", []), baseline.get("employees", []), kind="employee"),
        "departments": _compare_entities(current.get("departments", []), baseline.get("departments", []), kind="department"),
        "series": series,
        "methodology": "Сравнение выполняется с ближайшим snapshot не моложе выбранного периода. Если такого snapshot нет, используется самый ранний доступный и возвращается фактический интервал сравнения.",
    }
