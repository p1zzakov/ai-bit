# AI-BIT

Read-only Bitrix24 implementation audit through the official REST API.

## Current capabilities

- full snapshot of users, departments, CRM, tasks, groups and business-process templates;
- REST capability explorer by module;
- automatic findings with severity, impact and remediation;
- HTML best-practice report;
- raw JSON snapshots for further analysis;
- no write operations against Bitrix24.

## Deploy/update

```bash
cd /opt/ai-bit
git pull origin feat/mvp-bitrix-auditor
docker compose up -d --build
```

## Run

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/api/v1/explorer/run
curl -X POST http://localhost:8080/api/v1/audits/run
```

Open the latest report:

```text
http://SERVER_IP:8080/api/v1/reports/latest
```

JSON endpoints:

```text
GET /api/v1/explorer/latest
GET /api/v1/reports/latest/summary
GET /api/v1/reports/latest/findings
```

## Security

Use a temporary high-privilege incoming webhook only for discovery. Regenerate or delete it after the snapshot. Never commit `.env`, webhook URLs, credentials or tokens.

The application invokes read-only REST methods only. Rules marked as `heuristic` are expert thresholds, not official Bitrix24 limits.
