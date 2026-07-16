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

## Текущая версия

Browser Worker: `1.0.0-rc.5`.

## Что добавлено в rc.5

### Reports & Export

- единый управленческий отчёт по всем аналитическим контурам;
- Executive Summary;
- Enterprise Health и зрелость внедрения;
- операционные показатели, просрочка и сотрудники в зоне риска;
- Process Mining и кандидаты на автоматизацию;
- аудит бизнес-процессов, CRM-воронок и документооборота;
- ключевые рекомендации;
- план действий на 30 / 60 / 90 дней;
- экспорт в `HTML`, `JSON` и `PDF`;
- архив сформированных отчётов;
- вкладка **Отчёты** в Unified Enterprise Admin.

PDF формируется локально внутри контейнера через Chromium/Playwright. Внешние сервисы для конвертации не используются.

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
#system
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
- Reports & Export.

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
  "version": "1.0.0-rc.5"
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
http://SERVER_IP:8090/system                 System Health & Data Quality
```

## Reports & Export API

Сформировать новый отчёт:

```bash
curl -sS -X POST http://127.0.0.1:8090/reports/generate | jq
```

Список отчётов:

```bash
curl -sS http://127.0.0.1:8090/reports | jq
```

Скачать конкретный отчёт:

```text
GET /reports/{REPORT_ID}/html
GET /reports/{REPORT_ID}/json
GET /reports/{REPORT_ID}/pdf
```

Пример:

```bash
REPORT_ID=$(curl -sS http://127.0.0.1:8090/reports | jq -r '.[0].id')
curl -fSLo /tmp/ai-bit-report.pdf \
  "http://127.0.0.1:8090/reports/${REPORT_ID}/pdf"
```

Артефакты сохраняются в:

```text
/app/artifacts/reports/
```

При стандартном volume mapping на сервере:

```text
/opt/ai-bit/reports/ui/reports/
```

## Подготовка актуального отчёта

Перед генерацией рекомендуется обновить данные:

```bash
curl -sS -X POST http://127.0.0.1:8090/operations/collect -o /tmp/operations.json
curl -sS -X POST http://127.0.0.1:8090/business-architecture/collect -o /tmp/business-architecture.json
curl -sS -X POST http://127.0.0.1:8090/reports/generate | jq
```

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
GET  /reports
POST /reports/generate
GET  /reports/{report_id}/{format}
GET  /system
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

## Ограничения rc.5

- отчёт использует последние сохранённые данные и не запускает все сборы автоматически;
- качество отчёта зависит от свежести crawl, operational snapshot и Business Architecture Audit;
- план 30/60/90 строится по приоритетам рекомендаций и требует подтверждения владельцами процессов;
- PDF генерируется Chromium и может занимать несколько секунд;
- внутренние панели пока загружаются в iframe внутри единой оболочки;
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
- `1.0.0` — стабилизация, тесты и релизная документация.
