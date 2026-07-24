from __future__ import annotations

import hashlib
import json
from typing import Any

from ..storage.filesystem import FileSystemStorage
from .models import BrowserEvidence, BrowserEvidenceReceipt


class BrowserEvidenceService:
    NAMESPACE = "browser/evidence"
    LATEST_NAMESPACE = "browser/latest"

    def __init__(self, storage: FileSystemStorage) -> None:
        self.storage = storage

    @staticmethod
    def evidence_id(evidence: BrowserEvidence) -> str:
        canonical = json.dumps(
            evidence.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def ingest(self, evidence: BrowserEvidence) -> BrowserEvidenceReceipt:
        evidence_id = self.evidence_id(evidence)
        key = f"{evidence.name}/{evidence_id}"
        duplicate = self.storage.read_json(self.NAMESPACE, key) is not None
        if not duplicate:
            self.storage.write_json(
                self.NAMESPACE,
                key,
                {
                    "evidence_id": evidence_id,
                    "evidence": evidence.model_dump(mode="json"),
                },
            )
            self.storage.write_json(
                self.LATEST_NAMESPACE,
                evidence.name,
                {
                    "evidence_id": evidence_id,
                    "name": evidence.name,
                    "generated_at": evidence.generated_at,
                    "key": key,
                },
            )
        return BrowserEvidenceReceipt(
            status="duplicate" if duplicate else "accepted",
            evidence_id=evidence_id,
            name=evidence.name,
            generated_at=evidence.generated_at,
        )

    def latest(self, name: str) -> dict[str, Any] | None:
        metadata = self.storage.read_json(self.LATEST_NAMESPACE, name)
        if not metadata:
            return None
        return self.storage.read_json(self.NAMESPACE, str(metadata["key"]))
