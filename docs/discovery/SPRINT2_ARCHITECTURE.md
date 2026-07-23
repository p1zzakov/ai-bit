# AI-BIT Enterprise 6.2 — Sprint 2 Architecture

## Goal

Integrate read-only Discovery snapshots into the AI-BIT web system and make Active Directory evidence visible in the unified interface.

Sprint 2 is an ingestion and visualization sprint. It does not add new AD collectors.

## Current platform constraints

The current product is a monolithic FastAPI application with server-generated HTML modules and a unified iframe-based admin shell. Discovery must integrate with that model without coupling ingestion logic to the Bitrix browser worker.

## Target pipeline

```text
Windows Discovery Agent
        ↓ HTTPS/JSON
Discovery Ingestion API
        ↓ validation
Fingerprint Verification
        ↓
Snapshot Repository
        ↓
Projection Builder
        ↓
Infrastructure API
        ↓
/infrastructure UI
```

## Module boundaries

```text
browser-worker/
├── discovery/
│   ├── __init__.py
│   ├── models.py
│   ├── validation.py
│   ├── fingerprint.py
│   ├── repository.py
│   ├── service.py
│   ├── projections.py
│   ├── api.py
│   └── ui.py
├── data/
│   └── discovery/
│       ├── agents.json
│       ├── index.json
│       └── snapshots/
└── app.py
```

Sprint 2 uses a file-backed repository because the current platform does not have a shared relational persistence layer. The repository interface must be storage-agnostic so SQLite/PostgreSQL can be introduced later without changing the API contract.

## Storage model

### Agent record

```json
{
  "agent_id": "DS001",
  "display_name": "DS001",
  "source_type": "active_directory",
  "agent_version": "6.2.0",
  "first_seen_at_utc": "...",
  "last_seen_at_utc": "...",
  "last_snapshot_id": "...",
  "last_fingerprint": "...",
  "status": "online"
}
```

### Snapshot record

The original uploaded document is stored unchanged. A separate index stores metadata:

```json
{
  "snapshot_id": "...",
  "agent_id": "DS001",
  "received_at_utc": "...",
  "collected_at_utc": "...",
  "agent_version": "6.2.0",
  "schema_version": "1.1",
  "fingerprint": "...",
  "collector_status": {
    "ok": 5,
    "configuration_required": 0,
    "error": 0
  },
  "path": "snapshots/DS001/<snapshot_id>.json"
}
```

## Ingestion rules

1. The API never trusts client-calculated metadata.
2. `agent_id` must match `^[A-Za-z0-9._-]{1,128}$`.
3. Snapshot schema version must be supported.
4. The server recomputes SHA-256 over the canonical payload.
5. A fingerprint mismatch returns HTTP 422 and stores nothing.
6. Duplicate fingerprint for the same agent is idempotent and returns the existing snapshot.
7. Collector errors do not invalidate the whole snapshot.
8. Unknown collector types are retained as evidence.
9. Original snapshot JSON is immutable.
10. No ingestion endpoint may modify AD or any source system.

## Projections

The UI does not read raw JSON directly. Projection builders create read models:

- `agent_summary`;
- `forest_summary`;
- `domain_controller_summary`;
- `ou_tree`;
- `gpo_summary`;
- `snapshot_history`;
- `collector_health`.

Unknown data remains `unknown`; it is never converted to zero, false or missing.

## UI integration

A new navigation item is added to Unified Admin:

```text
Infrastructure
```

Route:

```text
/infrastructure
```

Initial Sprint 2 views:

1. Overview;
2. Discovery Agents;
3. Active Directory;
4. Domain Controllers;
5. Organizational Units;
6. Group Policies;
7. Snapshot History.

The first release uses the existing embedded HTML design system. A frontend framework migration is explicitly out of scope.

## Security

Sprint 2 development mode supports a shared bearer token configured through environment variables. The design reserves mTLS identity for Sprint 3.

Required controls:

- configurable request size limit;
- bearer token comparison using constant-time comparison;
- no secrets in responses or logs;
- immutable raw snapshot files;
- safe filename generation;
- atomic writes;
- rejection of path traversal;
- request correlation ID;
- ingestion audit log.

## Configuration

```env
DISCOVERY_ENABLED=true
DISCOVERY_DATA_DIR=/app/data/discovery
DISCOVERY_API_TOKEN=
DISCOVERY_MAX_UPLOAD_BYTES=10485760
DISCOVERY_ONLINE_WINDOW_MINUTES=90
```

## Sprint 2 non-goals

- Windows Service installation;
- automatic scheduling;
- mTLS enrollment;
- DNS, DHCP, replication, SYSVOL or Event Log collectors;
- AI findings and best-practice scoring;
- drift comparison;
- relational database migration.

## Definition of done

Sprint 2 is complete only when:

1. a real Sprint 1 snapshot is uploaded from the Windows host;
2. server fingerprint verification succeeds;
3. the snapshot is persisted and returned by history APIs;
4. all five collector statuses appear in AI-BIT;
5. forest, DC, OU and GPO data render in `/infrastructure`;
6. duplicate upload is idempotent;
7. invalid token and modified snapshot are rejected;
8. restart of the container does not lose snapshots;
9. a full deployment package and server-side test instructions are delivered.
