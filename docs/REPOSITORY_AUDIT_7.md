# AI-BIT Enterprise 7 — Repository Audit

Status: in progress  
Audit branch: `feature/platform-core-7.0`  
Production cutover: not completed

## 1. Current runtime map

The repository currently contains two application generations that must be treated as separate runtimes during migration.

| Runtime | Source | Compose file | Port | Status |
|---|---|---|---:|---|
| Legacy auditor | root `app/` and root `Dockerfile` | `docker-compose.yml` | 8080 | active |
| Legacy browser worker | `browser-worker/` | `docker-compose.yml` | 8090 | active, migration dependency |
| Platform Core 7 | `backend/` | `compose.platform.yml` | 8070 | active, new architecture |

`browser-worker/` is not removable yet. It still contains the Bitrix browser automation, dashboards, report generation and other operational modules that have not been migrated to Platform Core.

## 2. Authoritative architecture

New development belongs in:

- `backend/` — Platform Core API, storage, plugin registry and Infrastructure Discovery;
- `ad-agent/` — Windows read-only discovery agent;
- `plugins/` — future Platform Core plugins;
- `compose.platform.yml` — isolated Platform Core runtime;
- `.github/workflows/platform-core.yml` — Platform Core validation.

Legacy maintenance remains in:

- root `app/`;
- root `Dockerfile`;
- `browser-worker/`;
- `docker-compose.yml`;
- `reports/` and legacy data mounts.

The legacy paths are supported during migration but must not receive new platform features unless required for compatibility or production recovery.

## 3. Confirmed defect found during audit

### Browser worker restart loop on port 8090

`docker-compose.yml` executes `browser-worker/discovery_ingestion_patch.py` before Uvicorn. The patch previously searched for one exact FastAPI assignment:

```python
app = FastAPI(title="AI-BIT Browser Worker", version="0.2.0")
```

The browser-worker image applies many build-time patches before container startup. Any build patch that changes the FastAPI title, version or formatting makes the exact anchor disappear. The discovery patch then aborts, Uvicorn never starts and nothing binds to port 8090.

Fixed on this branch by making the patch locate a generic `app = FastAPI(...)` assignment and by validating the resulting Python source before startup.

## 4. Migration rules

1. Do not delete or move `browser-worker/` until all live routes and scheduled/reporting functions have owners in Platform Core.
2. Do not rename `compose.platform.yml` until Platform Core replaces both legacy services or a reverse proxy provides stable public routes.
3. Do not expose Platform Core as the replacement for port 8090 merely because it has an Infrastructure UI. Port 8090 currently represents the larger browser-worker application.
4. All new Discovery ingestion and graph development must use `backend/app/discovery/`; the legacy discovery package is compatibility-only.
5. Patch scripts are frozen except for production recovery. Their behavior must be covered by migration or build smoke checks before removal.

## 5. Required follow-up checks

- Build `browser-worker` from scratch and verify the discovery patch against the fully patched image.
- Verify endpoints on 8090: `/health`, `/api/v1/discovery/health`, `/login?force=true` and one read-only preset.
- Run Platform Core tests and container build.
- Inventory all browser-worker routes and map each route to: migrate, retain temporarily or retire.
- Inventory root auditor routes and data/report dependencies.
- Define a stable ingress plan for ports 8070, 8080 and 8090 before compose consolidation.

## 6. Removal gate

A legacy component can be removed only when:

- its routes and background operations are inventoried;
- replacement behavior exists and is tested;
- persistent data and volume ownership are documented;
- deployment and rollback commands are documented;
- the production host has passed a clean rebuild and smoke test.

Until those gates are met, repository cleanup means documentation, isolation and defect correction—not deletion.
