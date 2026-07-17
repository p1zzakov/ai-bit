# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Vision

Платформа обнаруживает проблемы, показывает evidence, объясняет причины и формирует приоритетный план цифровой трансформации на основе фактических данных портала.

## Principles

1. Только read-only работа с Bitrix24.
2. Каждый вывод должен иметь REST, Browser или Operational evidence.
3. Недостаток данных возвращается как `partial` или `insufficient_data`.
4. AI работает только по переданным фактам.
5. Рекомендации содержат проблему, действие и приоритет.
6. Оценки должны быть воспроизводимыми и объяснимыми.
7. Авторство и контакт разработчика отображаются централизованно и проверяются через Brand Integrity.

## Текущая версия

Browser Worker: `1.0.0-rc.7`.

## Что добавлено в rc.7

### Developer Attribution & Brand Integrity

- на все HTML-страницы автоматически добавляется единая подпись:

```text
Разработчик: Коваленко А.С. · pizzakov@gmail.com
```

- подпись внедряется централизованным middleware и не требует ручного копирования в каждый dashboard;
- HTML- и PDF-отчёты содержат данные разработчика;
- JSON-отчёт содержит секцию `developer`;
- `/health` содержит поля `product`, `developer`, `contact` и `brand_integrity`;
- `/system/health` показывает состояние Brand Integrity;
- при изменении обязательных метаданных система не ломается, а возвращает предупреждение;
- добавлены страница `/about` и API `/about/meta`;
- конфигурация проверяется контрольным SHA-256 digest.

Brand Integrity предназначен для обнаружения изменений обязательной подписи. Он не содержит намеренных механизмов отказа, саботажа или скрытой блокировки системы.

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```

Страница продукта:

```text
http://SERVER_IP:8090/about
```

Метаданные:

```bash
curl -sS http://127.0.0.1:8090/about/meta | jq
```

## Основные модули

- Implementation Audit;
- Deep Audit;
- Operational Intelligence;
- Operational Trends 7/30/90;
- Process Mining;
- Business Process Audit;
- CRM Funnel Audit;
- Document Flow Audit;
- System Health & Data Quality;
- Groq AI Coach;
- Reports & Export;
- Scheduling & Automation;
- Developer Attribution & Brand Integrity.

## Unified Enterprise Admin

```text
http://SERVER_IP:8090/
http://SERVER_IP:8090/admin
```

Разделы:

```text
#executive
#implementation
#operations
#processes
#architecture
#reports
#automation
#system
```

## Конфигурация

```env
BITRIX_WEBHOOK_URL=https://bitrix.example.kz/rest/USER_ID/SECRET/
BROWSER_BASE_URL=https://bitrix.example.kz
BROWSER_LOGIN_PATH=/auth/
BROWSER_LOGIN=ai-admin
BROWSER_PASSWORD=change-me
BROWSER_HEADLESS=true
BROWSER_TIMEOUT_MS=45000
BROWSER_IGNORE_HTTPS_ERRORS=false

AI_PROVIDER=groq
AI_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=

SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Almaty
SCHEDULER_POLL_SECONDS=30

SCHEDULER_OPERATIONS_ENABLED=true
SCHEDULER_OPERATIONS_SCHEDULE=daily@06:00

SCHEDULER_BUSINESS_ARCHITECTURE_ENABLED=true
SCHEDULER_BUSINESS_ARCHITECTURE_SCHEDULE=weekly:mon@07:00

SCHEDULER_CRAWL_ENABLED=true
SCHEDULER_CRAWL_SCHEDULE=weekly:sun@03:00

SCHEDULER_EXECUTIVE_REPORT_ENABLED=true
SCHEDULER_EXECUTIVE_REPORT_SCHEDULE=monthly:1@08:00
```

Webhook должен иметь read-доступ к CRM, пользователям, структуре, задачам и бизнес-процессам.

## Развёртывание

```bash
cd /opt/ai-bit
git switch agent/import-current-ai-bit
git pull
docker compose build --no-cache browser-worker
docker compose up -d browser-worker
```

Проверка:

```bash
curl -sS http://127.0.0.1:8090/health | jq
```

Ожидаем:

```json
{
  "status": "ok",
  "version": "1.0.0-rc.7",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com",
  "brand_integrity": {
    "status": "ok",
    "valid": true
  }
}
```

## Интерфейсы

```text
http://SERVER_IP:8090/                       Unified Enterprise Admin
http://SERVER_IP:8090/admin                  Unified Enterprise Admin
http://SERVER_IP:8090/executive              Executive Dashboard и AI Coach
http://SERVER_IP:8090/dashboard              Аудит внедрения
http://SERVER_IP:8090/operations             Operational Intelligence
http://SERVER_IP:8090/processes              Process Mining
http://SERVER_IP:8090/business-architecture  Business Architecture Audit
http://SERVER_IP:8090/reports-ui             Reports & Export
http://SERVER_IP:8090/automation             Scheduling & Automation
http://SERVER_IP:8090/system                 System Health & Data Quality
http://SERVER_IP:8090/about                  О системе и разработчике
```

## Brand Integrity API

```bash
curl -sS http://127.0.0.1:8090/about/meta | jq
curl -sS http://127.0.0.1:8090/system/health | jq '.brand_integrity,.developer'
curl -sS http://127.0.0.1:8090/health | jq '{product,developer,contact,brand_integrity}'
```

В нормальном состоянии:

```json
{
  "status": "ok",
  "valid": true,
  "marker": "ai-bit-developer-attribution",
  "message": "Developer attribution configuration is intact"
}
```

## Scheduling API

```bash
curl -sS http://127.0.0.1:8090/scheduler/status | jq
curl -sS -X POST http://127.0.0.1:8090/scheduler/run/operations | jq
curl -sS -X POST http://127.0.0.1:8090/scheduler/run/business_architecture | jq
curl -sS -X POST http://127.0.0.1:8090/scheduler/run/crawl | jq
curl -sS -X POST http://127.0.0.1:8090/scheduler/run/executive_report | jq
```

## Reports & Export API

```bash
curl -sS -X POST http://127.0.0.1:8090/reports/generate | jq
curl -sS http://127.0.0.1:8090/reports | jq
```

Форматы скачивания:

```text
GET /reports/{REPORT_ID}/html
GET /reports/{REPORT_ID}/json
GET /reports/{REPORT_ID}/pdf
```

Новые отчёты содержат подпись разработчика в HTML, PDF и JSON.

## System Health API

```bash
curl -sS http://127.0.0.1:8090/system/health | jq
```

## Groq AI Coach

AI Coach получает implementation audit, operational summary, тренды, Process Mining и Business Architecture Audit.

Примеры вопросов:

```text
Какие бизнес-процессы настроены неправильно и почему?
Какие стадии CRM-воронки нужно убрать или объединить?
Насколько готов документооборот?
Что автоматизировать в первую очередь?
```

## Основные API

```text
GET  /
GET  /admin
GET  /executive
GET  /dashboard
GET  /operations
GET  /processes
GET  /business-architecture
GET  /reports-ui
GET  /automation
GET  /system
GET  /health
GET  /about
GET  /about/meta
GET  /scheduler/status
POST /scheduler/run/{job_name}
GET  /reports
POST /reports/generate
GET  /reports/{report_id}/{format}
GET  /system/health
POST /operations/collect
GET  /operations/latest
GET  /operations/trends?days=7|30|90
GET  /process-mining/latest
POST /business-architecture/collect
GET  /business-architecture/latest
GET  /knowledge-graph/latest
GET  /ai/status
POST /ai/advice
```

## Ограничения rc.7

- Brand Integrity обнаруживает изменение централизованной конфигурации, но не блокирует работу системы;
- middleware применяется только к ответам `text/html`;
- ранее сформированные PDF не изменяются — подпись появится в новых отчётах;
- планировщик работает внутри процесса Browser Worker и требует постоянно запущенный контейнер;
- AI не заменяет подтверждение владельцем процесса.

## Roadmap

- `alpha.1` — Unified Knowledge Graph и AI Provider Layer;
- `alpha.2` — динамика 7/30/90 дней;
- `beta.1` — Executive Dashboard и AI Coach;
- `beta.2` — Process Mining;
- `rc.1` — Business Process, CRM Funnel и Document Flow Audit;
- `rc.2` — Unified Enterprise Admin;
- `rc.3` — System Health & Data Quality;
- `rc.4` — Enterprise UI Refresh;
- `rc.5` — Reports & Export;
- `rc.6` — Scheduling & Automation;
- `rc.7` — Developer Attribution & Brand Integrity;
- `1.0.0` — стабилизация, тесты и релизная документация;
- `2.0` — Digital Maturity, AI Consultant, ROI, HeatMap и Digital Twin.
