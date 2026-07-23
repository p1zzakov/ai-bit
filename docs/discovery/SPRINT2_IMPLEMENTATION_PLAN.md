# Sprint 2 Implementation Plan

## Delivery strategy

Sprint 2 is delivered through four controlled increments. Each increment must remain deployable and must not break the existing Bitrix24 audit routes.

## Increment 2.1 — Ingestion foundation

Deliverables:

- `discovery` Python package;
- Pydantic request and response models;
- configuration settings;
- bearer-token authentication;
- request-size enforcement;
- canonical JSON fingerprint verification;
- file-backed atomic repository;
- ingestion audit log;
- unit tests for validation, duplicate handling and tamper rejection.

Acceptance:

- valid real snapshot returns 201;
- repeated upload returns 200 duplicate;
- changed payload with old fingerprint returns 422;
- invalid token returns 401;
- persisted snapshot survives application restart.

## Increment 2.2 — Read APIs and projections

Deliverables:

- agents list;
- agent details;
- snapshot history;
- raw snapshot retrieval;
- Active Directory projection builder;
- OU tree builder;
- collector-health projection;
- summary counters.

Acceptance:

- Sprint 1 snapshot produces correct forest, DC, OU and GPO counts;
- missing collector data returns `unknown`, not zero;
- collector error is visible without hiding other evidence.

## Increment 2.3 — Infrastructure UI

Deliverables:

- `/infrastructure` page;
- navigation entry in Unified Admin;
- overview cards;
- agent status panel;
- DC table;
- OU hierarchy;
- GPO table;
- snapshot history;
- raw evidence drill-down.

Acceptance:

- UI renders inside existing Unified Admin without nested navigation;
- no existing dashboard route changes behaviour;
- page remains usable at desktop and narrow widths.

## Increment 2.4 — Agent upload command and deployment package

Deliverables:

- PowerShell upload script compatible with Windows PowerShell 5.1;
- agent configuration for endpoint, token and agent ID;
- TLS validation enabled by default;
- retry with bounded exponential backoff;
- no automatic deletion of local snapshot;
- complete server deployment package;
- acceptance-test script.

Acceptance:

- one command collects and uploads a snapshot;
- AI-BIT UI shows the uploaded data;
- network failure preserves the local snapshot and returns a clear error;
- upload retry does not create duplicates.

## Recommended repository implementation

```text
browser-worker/discovery/
  models.py
  settings.py
  canonical.py
  security.py
  repository.py
  projections.py
  service.py
  api.py
  ui.py

browser-worker/tests/discovery/
  test_canonical.py
  test_ingestion.py
  test_repository.py
  test_projections.py

ad-agent/src/
  DiscoveryTransport.psm1

ad-agent/scripts/
  Send-AIBitSnapshot.ps1
  Invoke-DiscoveryCycle.ps1
```

## Key decisions

1. Do not introduce PostgreSQL during Sprint 2.
2. Do not store only derived rows; retain immutable raw evidence.
3. Do not place Discovery implementation directly into `app.py` beyond router registration.
4. Do not trust the agent fingerprint without server recomputation.
5. Do not implement AI scoring before the ingestion and projection contracts are stable.
6. Do not call an agent `online` unless the latest upload is within the configured online window.

## Risks and mitigations

### Current monolithic application

Risk: regression in existing dashboards.

Mitigation: isolated package, router registration and additive navigation change only.

### File-backed storage concurrency

Risk: simultaneous writes corrupt index files.

Mitigation: process lock, temporary file, flush and atomic replace.

### Large snapshots

Risk: memory and disk pressure.

Mitigation: request-size limit, metadata index, retention policy in a later sprint.

### Agent identity spoofing

Risk: shared token does not provide per-agent identity.

Mitigation: acceptable for controlled Sprint 2 environment; mTLS enrollment is mandatory for production hardening.

### Fingerprint differences between PowerShell and Python

Risk: canonical JSON implementations diverge.

Mitigation: shared test vectors committed to the repository and verified by both runtimes before enabling uploads.

## Architecture gate

Implementation may begin only after the following are accepted:

- API envelope;
- schema compatibility policy;
- file-backed repository decision;
- shared-token limitation for Sprint 2;
- route `/infrastructure`;
- definition of done in `SPRINT2_ARCHITECTURE.md`.
