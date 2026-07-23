from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class DiscoverySnapshot(BaseModel):
    fingerprint_algorithm: str = "sha256"
    fingerprint: str = Field(min_length=64, max_length=64)
    payload: dict[str, Any]


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class InfrastructureGraph(BaseModel):
    agent_id: str
    snapshot_id: str
    fingerprint: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    summary: dict[str, Any]
