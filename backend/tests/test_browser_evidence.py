from __future__ import annotations

from pathlib import Path

from app.browser.models import BrowserEvidence
from app.browser.service import BrowserEvidenceService
from app.storage.filesystem import FileSystemStorage


def sample_evidence() -> BrowserEvidence:
    return BrowserEvidence(
        generated_at="2026-07-24T04:50:39+00:00",
        name="crm",
        url="https://example.invalid/crm/",
        title="CRM",
        headings=["CRM"],
        visible_text="CRM workspace",
    )


def test_browser_evidence_ingestion_is_idempotent(tmp_path: Path) -> None:
    service = BrowserEvidenceService(FileSystemStorage(tmp_path))
    first = service.ingest(sample_evidence())
    second = service.ingest(sample_evidence())

    assert first.status == "accepted"
    assert second.status == "duplicate"
    assert first.evidence_id == second.evidence_id


def test_browser_evidence_latest(tmp_path: Path) -> None:
    service = BrowserEvidenceService(FileSystemStorage(tmp_path))
    receipt = service.ingest(sample_evidence())
    latest = service.latest("crm")

    assert latest is not None
    assert latest["evidence_id"] == receipt.evidence_id
    assert latest["evidence"]["name"] == "crm"
