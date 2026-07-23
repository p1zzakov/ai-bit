from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_storage
from ..discovery.models import DiscoverySnapshot, InfrastructureGraph
from ..discovery.service import DiscoveryService
from ..storage.filesystem import FileSystemStorage

router = APIRouter(prefix="/discovery", tags=["discovery"])


def service(storage: FileSystemStorage = Depends(get_storage)) -> DiscoveryService:
    return DiscoveryService(storage)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Infrastructure Discovery"}


@router.post("/snapshots")
def ingest(snapshot: DiscoverySnapshot, discovery: DiscoveryService = Depends(service)) -> dict:
    return discovery.ingest(snapshot)


@router.get("/agents")
def agents(discovery: DiscoveryService = Depends(service)) -> list[dict]:
    return discovery.agents()


@router.get("/agents/{agent_id}/latest", response_model=DiscoverySnapshot)
def latest(agent_id: str, discovery: DiscoveryService = Depends(service)) -> DiscoverySnapshot:
    return discovery.latest(agent_id)


@router.get("/agents/{agent_id}/graph", response_model=InfrastructureGraph)
def graph(agent_id: str, discovery: DiscoveryService = Depends(service)) -> InfrastructureGraph:
    return discovery.graph(agent_id)
