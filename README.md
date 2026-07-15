# AI-BIT

Read-only audit platform for Bitrix24 and future enterprise infrastructure connectors.

## MVP capabilities

- FastAPI health endpoint;
- read-only Bitrix24 webhook connection check;
- initial collection of profile, users, departments, CRM statuses and CRM fields;
- JSON audit report generation;
- Docker Compose deployment.

## Server deployment

```bash
git clone https://github.com/p1zzakov/ai-bit.git
cd ai-bit
git checkout feat/mvp-bitrix-auditor
cp .env.example .env
nano .env

docker compose up -d --build
docker compose logs -f auditor
```

Check the service:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/bitrix/status
curl -X POST http://localhost:8080/api/v1/audits/run
```

Reports are written to `./reports` on the host.

## Security

Use a dedicated inbound Bitrix24 webhook with the minimum required permissions. The application currently performs only read operations. Never commit `.env`, webhook URLs or access tokens.
