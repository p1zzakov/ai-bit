from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..browser.models import BrowserEvidence, BrowserEvidenceReceipt
from ..browser.service import BrowserEvidenceService
from ..dependencies import get_storage
from ..storage.filesystem import FileSystemStorage

router = APIRouter(prefix="/browser", tags=["browser"])


def service(storage: FileSystemStorage = Depends(get_storage)) -> BrowserEvidenceService:
    return BrowserEvidenceService(storage)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Browser Evidence"}


@router.post("/evidence", response_model=BrowserEvidenceReceipt)
def ingest(
    evidence: BrowserEvidence,
    browser: BrowserEvidenceService = Depends(service),
) -> BrowserEvidenceReceipt:
    return browser.ingest(evidence)


@router.get("/evidence/{name}")
def latest(name: str, browser: BrowserEvidenceService = Depends(service)) -> dict:
    result = browser.latest(name)
    if result is None:
        raise HTTPException(status_code=404, detail="Browser evidence not found")
    return result
