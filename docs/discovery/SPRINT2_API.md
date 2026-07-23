# Discovery API Contract — Sprint 2

Base path:

```text
/api/v1/discovery
```

## Authentication

Agent ingestion requests use:

```http
Authorization: Bearer <DISCOVERY_API_TOKEN>
```

Read endpoints initially inherit the existing AI-BIT access boundary.

## POST /snapshots

Uploads one immutable Discovery snapshot.

### Request

```json
{
  "agent_id": "DS001",
  "display_name": "DS001",
  "source_type": "active_directory",
  "snapshot": {
    "fingerprint_algorithm": "sha256",
    "fingerprint": "64-character lowercase hex",
    "payload": {}
  }
}
```

### Created response — 201

```json
{
  "status": "created",
  "agent_id": "DS001",
  "snapshot_id": "...",
  "fingerprint": "...",
  "received_at_utc": "...",
  "collector_status": {
    "ok": 5,
    "configuration_required": 0,
    "error": 0,
    "skipped": 0
  }
}
```

### Duplicate response — 200

```json
{
  "status": "duplicate",
  "agent_id": "DS001",
  "snapshot_id": "existing-id",
  "fingerprint": "..."
}
```

### Errors

- `401`: missing or invalid token;
- `413`: request exceeds configured limit;
- `422`: invalid envelope, unsupported schema or fingerprint mismatch;
- `503`: Discovery is disabled or storage unavailable.

## GET /agents

Returns registered agents and current status.

```json
{
  "items": [
    {
      "agent_id": "DS001",
      "display_name": "DS001",
      "source_type": "active_directory",
      "agent_version": "6.2.0",
      "last_seen_at_utc": "...",
      "last_snapshot_id": "...",
      "status": "online",
      "summary": {
        "forest": "corp.kelet.kz",
        "domains": 1,
        "domain_controllers": 2,
        "organizational_units": 31,
        "group_policies": 47
      }
    }
  ]
}
```

## GET /agents/{agent_id}

Returns agent details and latest projection.

## GET /agents/{agent_id}/snapshots

Returns snapshot metadata in reverse chronological order.

Query parameters:

- `limit`: 1–100, default 20;
- `before`: optional UTC timestamp.

## GET /snapshots/{snapshot_id}

Returns raw immutable snapshot evidence.

## GET /agents/{agent_id}/projection

Returns UI-ready projection:

```json
{
  "agent": {},
  "snapshot": {},
  "collector_health": [],
  "active_directory": {
    "forest": {},
    "domains": [],
    "domain_controllers": [],
    "organizational_units": [],
    "ou_tree": [],
    "group_policies": []
  }
}
```

## GET /health

```json
{
  "status": "ok",
  "enabled": true,
  "storage_writable": true,
  "agents": 1,
  "snapshots": 3
}
```

## Canonical fingerprint verification

The server takes `snapshot.payload`, recursively sorts object properties, serializes compact UTF-8 JSON and computes SHA-256. The result must equal `snapshot.fingerprint`.

Array order is preserved because source order may be evidence. Collector implementations are responsible for deterministic ordering where appropriate.

## Compatibility policy

Supported in Sprint 2:

- agent version `6.2.x`;
- snapshot schema `1.1`;
- fingerprint algorithm `sha256`.

Unsupported future versions return `422 unsupported_schema_version` rather than being partially interpreted.
