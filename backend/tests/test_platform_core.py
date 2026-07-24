from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.storage.filesystem import FileSystemStorage


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"].startswith("7.0.0")


def test_filesystem_storage_roundtrip(tmp_path: Path) -> None:
    storage = FileSystemStorage(tmp_path)
    storage.write_json("snapshots", "sample", {"value": 42})
    assert storage.read_json("snapshots", "sample") == {"value": 42}
    assert storage.list_keys("snapshots") == ["sample"]


def test_filesystem_storage_rejects_traversal(tmp_path: Path) -> None:
    storage = FileSystemStorage(tmp_path)
    try:
        storage.write_json("../outside", "sample", {"value": 42})
    except ValueError:
        return
    raise AssertionError("Path traversal must be rejected")
