from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiscoverySettings:
    storage_dir: Path
    api_token: str
    max_payload_bytes: int


def load_settings() -> DiscoverySettings:
    return DiscoverySettings(
        storage_dir=Path(os.getenv("DISCOVERY_STORAGE_DIR", "/app/data/discovery")),
        api_token=os.getenv("DISCOVERY_API_TOKEN", "").strip(),
        max_payload_bytes=int(os.getenv("DISCOVERY_MAX_PAYLOAD_BYTES", "10485760")),
    )
