from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException

from ..storage.filesystem import FileSystemStorage
from .models import DiscoverySnapshot, GraphEdge, GraphNode, InfrastructureGraph

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def safe_id(value: str) -> str:
    return _SAFE.sub("_", value).strip("._") or "unknown"


class DiscoveryService:
    def __init__(self, storage: FileSystemStorage) -> None:
        self.storage = storage

    def ingest(self, snapshot: DiscoverySnapshot) -> dict[str, Any]:
        payload = snapshot.payload
        if payload.get("schema_version") != "1.1":
            raise HTTPException(422, "Unsupported discovery schema_version")
        calculated = fingerprint_payload(payload)
        if calculated != snapshot.fingerprint.lower():
            raise HTTPException(422, "Snapshot fingerprint mismatch")
        host = payload.get("host") or {}
        agent_id = safe_id(str(host.get("computer_name") or "unknown"))
        key = f"discovery/snapshots/{agent_id}/{calculated}.json"
        duplicate = self.storage.exists(key)
        if not duplicate:
            self.storage.write_json(key, snapshot.model_dump(mode="json"))
            latest = {
                "agent_id": agent_id,
                "fingerprint": calculated,
                "snapshot_id": payload.get("snapshot_id"),
                "collected_at_utc": payload.get("collected_at_utc"),
                "stored_at_utc": datetime.now(UTC).isoformat(),
                "key": key,
            }
            self.storage.write_json(f"discovery/latest/{agent_id}.json", latest)
        return {
            "status": "duplicate" if duplicate else "accepted",
            "agent_id": agent_id,
            "snapshot_id": payload.get("snapshot_id"),
            "fingerprint": calculated,
            "collectors": len(payload.get("collectors") or []),
        }

    def latest(self, agent_id: str) -> DiscoverySnapshot:
        metadata = self.storage.read_json(f"discovery/latest/{safe_id(agent_id)}.json")
        return DiscoverySnapshot.model_validate(self.storage.read_json(metadata["key"]))

    def agents(self) -> list[dict[str, Any]]:
        result = []
        for key in self.storage.list_keys("discovery/latest"):
            result.append(self.storage.read_json(key))
        return sorted(result, key=lambda row: row.get("stored_at_utc", ""), reverse=True)

    def graph(self, agent_id: str) -> InfrastructureGraph:
        snapshot = self.latest(agent_id)
        payload = snapshot.payload
        collectors = {item.get("name"): item for item in payload.get("collectors") or []}
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        forest_data = (collectors.get("forest") or {}).get("data") or {}
        forest_name = forest_data.get("name") or forest_data.get("root_domain")
        forest_id = f"forest:{forest_name}" if forest_name else None
        if forest_id:
            nodes.append(GraphNode(id=forest_id, type="forest", label=str(forest_name), properties=forest_data))

        domains = (collectors.get("domains") or {}).get("data") or []
        for domain in domains:
            name = domain.get("dns_root") or domain.get("distinguished_name")
            node_id = f"domain:{name}"
            nodes.append(GraphNode(id=node_id, type="domain", label=str(name), properties=domain))
            if forest_id:
                edges.append(GraphEdge(source=forest_id, target=node_id, relation="contains"))

        dcs = (collectors.get("domain_controllers") or {}).get("data") or []
        for dc in dcs:
            label = dc.get("hostname") or dc.get("name")
            node_id = f"domain_controller:{label}"
            nodes.append(GraphNode(id=node_id, type="domain_controller", label=str(label), properties=dc))
            domain = dc.get("domain")
            if domain:
                edges.append(GraphEdge(source=f"domain:{domain}", target=node_id, relation="hosts"))

        ous = (collectors.get("organizational_units") or {}).get("data") or []
        for ou in ous:
            dn = ou.get("distinguished_name")
            node_id = f"ou:{dn}"
            nodes.append(GraphNode(id=node_id, type="organizational_unit", label=str(ou.get("name") or dn), properties=ou))
            if domains:
                edges.append(GraphEdge(source=f"domain:{domains[0].get('dns_root')}", target=node_id, relation="contains"))

        gpos = (collectors.get("gpo_summary") or {}).get("data") or []
        for gpo in gpos:
            gid = gpo.get("id") or gpo.get("display_name")
            node_id = f"gpo:{gid}"
            nodes.append(GraphNode(id=node_id, type="group_policy", label=str(gpo.get("display_name") or gid), properties=gpo))
            domain = gpo.get("domain_name")
            if domain:
                edges.append(GraphEdge(source=f"domain:{domain}", target=node_id, relation="defines"))

        statuses = [item.get("status") for item in payload.get("collectors") or []]
        health = 100 if statuses and all(status == "ok" for status in statuses) else 70
        summary = {
            "forest": forest_name,
            "domains": len(domains),
            "domain_controllers": len(dcs),
            "organizational_units": len(ous),
            "group_policies": len(gpos),
            "health_score": health,
        }
        return InfrastructureGraph(agent_id=agent_id, snapshot_id=str(payload.get("snapshot_id")), fingerprint=snapshot.fingerprint, nodes=nodes, edges=edges, summary=summary)
