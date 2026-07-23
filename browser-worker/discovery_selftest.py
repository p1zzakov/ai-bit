from __future__ import annotations

import tempfile
from pathlib import Path

from discovery.canonical import sha256_payload
from discovery.models import DiscoverySnapshot
from discovery.repository import DiscoveryRepository
from discovery.service import DiscoveryService


def main() -> None:
    payload = {
        "schema_version": "1.1",
        "agent_version": "6.2.0",
        "snapshot_id": "00000000-0000-0000-0000-000000000001",
        "collected_at_utc": "2026-07-23T00:00:00Z",
        "host": {"computer_name": "DS001"},
        "collectors": [{"name": "forest", "status": "ok", "data": {"name": "corp.kelet.kz"}}],
    }
    fingerprint = sha256_payload(payload)
    snapshot = DiscoverySnapshot(
        fingerprint_algorithm="sha256",
        fingerprint=fingerprint,
        payload=payload,
    )

    with tempfile.TemporaryDirectory() as directory:
        service = DiscoveryService(DiscoveryRepository(Path(directory)))
        first = service.ingest(snapshot)
        second = service.ingest(snapshot)
        assert first.status == "accepted"
        assert second.status == "duplicate"
        assert first.agent_id == "DS001"
        assert len(service.repository.list_snapshots()) == 1

    print("Discovery ingestion self-test: OK")


if __name__ == "__main__":
    main()
