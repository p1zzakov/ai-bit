from __future__ import annotations

import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Query

from .models import DiscoverySnapshot, IngestionReceipt, SnapshotSummary
from .repository import DiscoveryRepository
from .service import DiscoveryService
from .settings import load_settings

settings = load_settings()
repository = DiscoveryRepository(settings.storage_dir)
service = DiscoveryService(repository)
router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


def authorize(token: str | None) -> None:
    if not settings.api_token:
        return
    if token is None or not hmac.compare_digest(token, settings.api_token):
        raise HTTPException(status_code=401, detail="Invalid discovery API token")


@router.get("/health")
def discovery_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "AI-BIT Discovery Ingestion",
        "storage_dir": str(settings.storage_dir),
        "authentication_required": bool(settings.api_token),
        "supported_schema_versions": ["1.1"],
    }


@router.post("/snapshots", response_model=IngestionReceipt)
def upload_snapshot(
    snapshot: DiscoverySnapshot,
    x_aibit_token: Annotated[str | None, Header()] = None,
    x_aibit_agent_id: Annotated[str | None, Header()] = None,
) -> IngestionReceipt:
    authorize(x_aibit_token)
    return service.ingest(snapshot, agent_id=x_aibit_agent_id)


@router.get("/snapshots", response_model=list[SnapshotSummary])
def list_snapshots(
    agent_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    x_aibit_token: Annotated[str | None, Header()] = None,
) -> list[SnapshotSummary]:
    authorize(x_aibit_token)
    return [SnapshotSummary.model_validate(item) for item in repository.list_snapshots(agent_id, limit)]


@router.get("/snapshots/{agent_id}/{fingerprint}")
def get_snapshot(
    agent_id: str,
    fingerprint: str,
    x_aibit_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    authorize(x_aibit_token)
    document = repository.read(agent_id, fingerprint)
    if document is None:
        raise HTTPException(status_code=404, detail="Discovery snapshot not found")
    return document
