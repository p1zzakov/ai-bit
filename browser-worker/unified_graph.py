from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _node_id(kind: str, value: Any) -> str:
    return f"{kind}:{value}"


def build_unified_graph(crawl: dict[str, Any] | None, operations: dict[str, Any] | None) -> dict[str, Any]:
    crawl = crawl or {}
    operations = operations or {}
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_node(node: dict[str, Any]) -> None:
        node_id = str(node["id"])
        if node_id not in seen:
            seen.add(node_id)
            nodes.append(node)

    for page in crawl.get("nodes", []):
        page_id = _node_id("page", page.get("url"))
        section = str(page.get("section") or "other")
        module_id = _node_id("module", section)
        add_node({"id": module_id, "type": "module", "name": section})
        add_node({"id": page_id, "type": "page", "name": page.get("title") or page.get("url"), "url": page.get("url"), "status": page.get("status"), "section": section})
        edges.append({"from": module_id, "to": page_id, "type": "contains"})

    for employee in operations.get("employees", []):
        employee_id = _node_id("user", employee.get("id"))
        add_node({"id": employee_id, "type": "user", "name": employee.get("name"), "risk": employee.get("risk"), "metrics": {k: employee.get(k) for k in ("open_tasks", "overdue_tasks", "without_deadline", "completed_tasks", "overdue_rate", "risk_score")}})
        for department_id, department_name in zip(employee.get("department_ids") or [], employee.get("departments") or []):
            dept_id = _node_id("department", department_id)
            add_node({"id": dept_id, "type": "department", "name": department_name})
            edges.append({"from": employee_id, "to": dept_id, "type": "member_of"})

    for department in operations.get("departments", []):
        dept_id = _node_id("department", department.get("id"))
        add_node({"id": dept_id, "type": "department", "name": department.get("name"), "risk": department.get("risk"), "metrics": {k: department.get(k) for k in ("employees", "open", "overdue", "without_deadline", "completed", "overdue_rate")}})

    recommendations = []
    for source, items in (("implementation", crawl.get("assessment", {}).get("recommendations", [])), ("deep_audit", crawl.get("deep_audit", {}).get("action_plan", [])), ("operations", operations.get("recommendations", []))):
        for index, item in enumerate(items):
            rec_id = _node_id("recommendation", f"{source}:{index}")
            title = item.get("title") or item.get("module") or "Рекомендация"
            recommendation = {"id": rec_id, "type": "recommendation", "source": source, "name": title, "priority": item.get("priority") or item.get("severity"), "action": item.get("action") or item.get("recommendation"), "finding": item.get("finding")}
            add_node(recommendation)
            recommendations.append(recommendation)

    counts: dict[str, int] = {}
    for node in nodes:
        counts[node["type"]] = counts.get(node["type"], 0) + 1

    return {"version": "1.0.0-alpha.1", "generated_at": datetime.now(UTC).isoformat(), "summary": {"nodes": len(nodes), "edges": len(edges), "by_type": counts, "recommendations": len(recommendations)}, "nodes": nodes, "edges": edges, "recommendations": recommendations}


def save_unified_graph(artifacts_dir: Path, graph: dict[str, Any]) -> Path:
    root = artifacts_dir / "knowledge-graph"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "latest.json"
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
