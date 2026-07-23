from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DiscoverySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fingerprint_algorithm: Literal["sha256"]
    fingerprint: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    payload: dict[str, Any]


class IngestionReceipt(BaseModel):
    status: Literal["accepted", "duplicate"]
    agent_id: str
    snapshot_id: str
    fingerprint: str
    stored_at_utc: str
    collectors: int


class SnapshotSummary(BaseModel):
    agent_id: str
    snapshot_id: str
    fingerprint: str
    collected_at_utc: str
    stored_at_utc: str
    schema_version: str
    agent_version: str
    collector_statuses: dict[str, int]
