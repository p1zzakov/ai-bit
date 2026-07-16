# AI-BIT

AI-BIT — read-only платформа технического, функционального и операционного аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `0.9.0`.

## Архитектура

AI-BIT объединяет пять контуров:

- **REST Collector** — пользователи, подразделения, задачи, CRM и другие сущности;
- **Browser Worker** — UI-разделы и настройки, которых нет в REST;
- **Portal Crawler** — карта внутренних страниц;
- **Deep Audit** — рекомендации по модулям и страницам;
- **Operational Intelligence** — нагрузка сотрудников, просрочка, дисциплина сроков и риски подразделений.

Все операции против Bitrix24 выполняются в read-only режиме.

## Возможности 0.9.0

### Аудит внедрения

- implementation score;
- матрица используемых и недоступных модулей;
- deep audit CRM, задач, структуры, процессов, диска и других разделов;
- рекомендации по каждой обнаруженной странице;
- приоритетный план оптимизации;
- история crawl-запусков и diff.

### Operational Intelligence

- активные пользователи и подразделения;
- открытые и завершённые задачи;
- просроченные задачи и доля просрочки;
- задачи без крайнего срока;
- средний возраст открытых задач;
- среднее время закрытия;
- нагрузка и риск перегрузки сотрудников;
- аналитика подразделений;
- управленческие рекомендации;
- сохранение operational snapshots для дальнейшей динамики.

Operational Intelligence не является рейтингом ценности сотрудников. Метрики показывают дисциплину исполнения, качество планирования и риск перегрузки.

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

Ожидаемая версия:

```json
{
  "version": "0.9.0"
}
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
```

Webhook должен иметь read-доступ минимум к пользователям, структуре компании и задачам.

Не коммитьте `.env`, webhook URL, пароли, токены и browser storage state.

## Dashboard

Аудит внедрения:

```text
http://SERVER_IP:8090/dashboard
```

Operational Intelligence:

```text
http://SERVER_IP:8090/operations
```

## Operational Intelligence API

Собрать свежий snapshot:

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/operations/collect \
  | jq
```

Получить последний snapshot:

```bash
curl -sS \
  http://127.0.0.1:8090/operations/latest \
  | jq
```

Краткая сводка:

```bash
curl -sS \
  http://127.0.0.1:8090/operations/latest \
  | jq '.summary'
```

Сотрудники с высоким риском:

```bash
curl -sS \
  http://127.0.0.1:8090/operations/latest \
  | jq '.employees[] | select(.risk == "critical" or .risk == "high")'
```

## Crawler

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/crawl \
  -H 'Content-Type: application/json' \
  -d '{
    "start_path": "/",
    "max_pages": 150,
    "max_depth": 3,
    "include_query": false,
    "save_html": false,
    "delay_ms": 300
  }' \
  -o /tmp/crawl.json
```

## Основные API

```text
GET  /health
POST /login
POST /crawl
GET  /crawl/history
GET  /crawl/assessment/latest
GET  /crawl/deep-audit/latest
GET  /crawl/diff
GET  /dashboard
GET  /operations
POST /operations/collect
GET  /operations/latest
```

## Артефакты

```text
/app/artifacts/history/crawl-*.json
/app/artifacts/operations/operations-*.json
/app/artifacts/operations/latest.json
/app/artifacts/latest-crawl.json
```

При стандартном compose volume данные находятся на host в:

```text
/opt/ai-bit/reports/ui/
```

## Ограничения 0.9.0

- аналитика зависит от прав webhook;
- текущая версия анализирует задачи, доступные webhook-пользователю;
- сложность и бизнес-ценность задач пока не оцениваются;
- показатели сотрудника нельзя использовать как самостоятельную кадровую оценку;
- динамика между operational snapshots будет визуализирована в `1.0.0`;
- CRM-воронки, роботы и триггеры требуют отдельного расширения REST collector.

## Roadmap 1.0.0 — AI Management Advisor

- единый Browser + REST knowledge graph;
- Executive Dashboard;
- динамика 7/30/90 дней;
- process mining;
- анализ CRM-воронок, стадий, роботов и триггеров;
- выявление повторяющихся ручных операций;
- оценка потенциального эффекта автоматизации;
- AI Coach: проблема → причина → решение → риск → эффект;
- управленческий PDF/Excel отчёт;
- план цифровой трансформации.

## Правило разработки

1. изменения выполняются в ветке;
2. commit и push;
3. `git pull` на сервере;
4. пересборка контейнера;
5. smoke test;
6. merge после проверки.
