from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException

from .canonical import sha256_payload
from .models import DiscoverySnapshot, IngestionReceipt
from .repository import DiscoveryRepository


class DiscoveryService:
    def __init__(self, repository: DiscoveryRepository) -> None:
        self.repository = repository

    def ingest(self, snapshot: DiscoverySnapshot, agent_id: str | None = None) -> IngestionReceipt:
        payload = snapshot.payload
        resolved_agent = (agent_id or payload.get("host", {}).get("computer_name") or "unknown").strip()
        snapshot_id = str(payload.get("snapshot_id") or "")
        schema_version = str(payload.get("schema_version") or "")
        if not snapshot_id:
            raise HTTPException(status_code=422, detail="payload.snapshot_id is required")
        if schema_version not in {"1.1"}:
            raise HTTPException(status_code=422, detail=f"Unsupported schema_version: {schema_version}")

        expected = sha256_payload(payload)
        supplied = snapshot.fingerprint.lower()
        if expected != supplied:
            raise HTTPException(
                status_code=422,
                detail={"code": "fingerprint_mismatch", "expected": expected, "supplied": supplied},
            )

        collectors = payload.get("collectors", [])
        if not isinstance(collectors, list):
            raise HTTPException(status_code=422, detail="payload.collectors must be an array")

        if self.repository.exists(resolved_agent, supplied):
            existing = self.repository.read(resolved_agent, supplied) or {}
            stored_at = existing.get("ingestion", {}).get("stored_at_utc") or datetime.now(UTC).isoformat()
            return IngestionReceipt(
                status="duplicate",
                agent_id=resolved_agent,
                snapshot_id=snapshot_id,
                fingerprint=supplied,
                stored_at_utc=stored_at,
                collectors=len(collectors),
            )

        _, stored_at = self.repository.store(resolved_agent, snapshot.model_dump())
        return IngestionReceipt(
            status="accepted",
            agent_id=resolved_agent,
            snapshot_id=snapshot_id,
            fingerprint=supplied,
            stored_at_utc=stored_at,
            collectors=len(collectors),
        )
