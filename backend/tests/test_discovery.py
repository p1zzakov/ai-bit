from __future__ import annotations

from fastapi.testclient import TestClient

from app.dependencies import get_storage
from app.discovery.service import fingerprint_payload
from app.main import create_app
from app.storage.filesystem import FileSystemStorage


def sample_snapshot() -> dict:
    payload = {
        "schema_version": "1.1",
        "agent_version": "6.2.0",
        "snapshot_id": "test-snapshot",
        "collected_at_utc": "2026-07-23T00:00:00Z",
        "host": {"computer_name": "DS001"},
        "collectors": [
            {"name": "forest", "status": "ok", "data": {"name": "corp.kelet.kz", "root_domain": "corp.kelet.kz"}},
            {"name": "domains", "status": "ok", "data": [{"dns_root": "corp.kelet.kz"}]},
            {"name": "domain_controllers", "status": "ok", "data": [{"hostname": "DS001.corp.kelet.kz", "domain": "corp.kelet.kz"}]},
            {"name": "organizational_units", "status": "ok", "data": [{"name": "IT", "distinguished_name": "OU=IT,DC=corp,DC=kelet,DC=kz"}]},
            {"name": "gpo_summary", "status": "ok", "data": [{"id": "gpo-1", "display_name": "Security Baseline", "domain_name": "corp.kelet.kz"}]},
        ],
    }
    return {"fingerprint_algorithm": "sha256", "fingerprint": fingerprint_payload(payload), "payload": payload}


def test_discovery_ingestion_and_graph(tmp_path) -> None:
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: FileSystemStorage(tmp_path)
    client = TestClient(app)
    snapshot = sample_snapshot()

    accepted = client.post("/api/v1/discovery/snapshots", json=snapshot)
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    duplicate = client.post("/api/v1/discovery/snapshots", json=snapshot)
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"

    agents = client.get("/api/v1/discovery/agents").json()
    assert agents[0]["agent_id"] == "DS001"

    graph = client.get("/api/v1/discovery/agents/DS001/graph")
    assert graph.status_code == 200
    body = graph.json()
    assert body["summary"]["forest"] == "corp.kelet.kz"
    assert body["summary"]["health_score"] == 100
    assert len(body["nodes"]) == 5
