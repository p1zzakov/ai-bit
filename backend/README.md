# AI-BIT Enterprise 7 — Platform Core

Stage 1 introduces a modular FastAPI runtime alongside the legacy application. It does not replace port 8090 yet.

## Architecture

```text
app/main.py
  ├── api/router.py
  ├── core/config.py
  ├── core/lifecycle.py
  ├── storage/base.py
  ├── storage/filesystem.py
  └── plugins/registry.py
```

## Run with Docker

```bash
docker compose -f compose.platform.yml build --no-cache platform-core
docker compose -f compose.platform.yml up -d platform-core
curl -sS http://127.0.0.1:8070/api/v1/system/health
```

## Run tests

```bash
cd backend
python -m pip install -e '.[test]'
pytest -q
```

## Stage 1 boundaries

Included: typed configuration, logging, lifecycle, router registry, storage abstraction, atomic filesystem storage, plugin contract, plugin registry, health API and isolated Docker runtime.

Not included: migration of legacy Bitrix routes, Discovery ingestion, UI, authentication, PostgreSQL or production traffic cutover.
