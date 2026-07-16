# AI-BIT

AI-BIT — read-only платформа технического, функционального и операционного аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `1.0.0-alpha.2`.

## Архитектура

AI-BIT объединяет восемь контуров:

- **REST Collector** — пользователи, подразделения, задачи, CRM и другие сущности;
- **Browser Worker** — UI-разделы и настройки, которых нет в REST;
- **Portal Crawler** — карта внутренних страниц;
- **Deep Audit** — рекомендации по модулям и страницам;
- **Operational Intelligence** — нагрузка, просрочка и риски подразделений;
- **Operational Trends** — динамика 7/30/90 дней;
- **Unified Knowledge Graph** — связь пользователей, подразделений, модулей, страниц и рекомендаций;
- **AI Provider Layer** — экспертные рекомендации через Groq с возможностью смены провайдера.

Все операции против Bitrix24 выполняются в read-only режиме.

## Возможности 1.0.0-alpha.2

- история operational snapshot;
- сравнение текущего состояния с периодами 7, 30 и 90 дней;
- динамика открытых и просроченных задач;
- изменение доли просрочки;
- динамика задач без срока;
- изменение количества сотрудников в зоне риска;
- сотрудники и подразделения с улучшением или ухудшением;
- вход в зону риска и выход из неё;
- визуализация трендов на `/operations`;
- передача 30-дневного тренда в AI Coach;
- сохранение Unified Knowledge Graph и Deep Audit из предыдущих версий.

Если snapshot требуемой давности отсутствует, система использует самый ранний доступный snapshot и возвращает фактический интервал сравнения.

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

Не коммитьте `.env`, webhook URL, пароли, токены, Groq API key и browser storage state.

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
  "version": "1.0.0-alpha.2"
}
```

## Dashboard

```text
http://SERVER_IP:8090/dashboard
http://SERVER_IP:8090/operations
```

Во вкладке **Динамика** доступны переключатели 7, 30 и 90 дней.

## Operational Intelligence API

Собрать свежий snapshot:

```bash
curl -sS -X POST http://127.0.0.1:8090/operations/collect | jq '.summary'
```

Последний snapshot:

```bash
curl -sS http://127.0.0.1:8090/operations/latest | jq '.summary'
```

История snapshot:

```bash
curl -sS 'http://127.0.0.1:8090/operations/history?limit=30' | jq
```

Тренд за 7 дней:

```bash
curl -sS 'http://127.0.0.1:8090/operations/trends?days=7' | jq
```

Тренд за 30 дней:

```bash
curl -sS 'http://127.0.0.1:8090/operations/trends?days=30' | jq
```

Тренд за 90 дней:

```bash
curl -sS 'http://127.0.0.1:8090/operations/trends?days=90' | jq
```

Краткая сводка тренда:

```bash
curl -sS 'http://127.0.0.1:8090/operations/trends?days=30' \
  | jq '{status,direction,actual_comparison_days,deltas}'
```

Сотрудники с ухудшением:

```bash
curl -sS 'http://127.0.0.1:8090/operations/trends?days=30' \
  | jq '.employees.worsened'
```

Подразделения с улучшением:

```bash
curl -sS 'http://127.0.0.1:8090/operations/trends?days=30' \
  | jq '.departments.improved'
```

## Unified Knowledge Graph API

```bash
curl -sS http://127.0.0.1:8090/knowledge-graph/latest | jq '.summary'
```

Артефакт сохраняется в:

```text
/app/artifacts/knowledge-graph/latest.json
```

## AI API

Статус провайдера:

```bash
curl -sS http://127.0.0.1:8090/ai/status | jq
```

Получить управленческую рекомендацию с учётом 30-дневной динамики:

```bash
curl -sS -X POST \
  --get \
  --data-urlencode 'question=Проанализируй динамику за 30 дней и предложи приоритетные действия' \
  http://127.0.0.1:8090/ai/advice \
  | jq
```

Интеграция использует официальный Python SDK `groq`. AI получает агрегированные показатели, тренды, рекомендации и audit evidence.

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
GET  /operations/history
GET  /operations/trends?days=7|30|90
GET  /knowledge-graph/latest
GET  /ai/status
POST /ai/advice
```

## Ограничения alpha.2

- тренды появляются после накопления минимум двух operational snapshot;
- для полноценного сравнения 7/30/90 дней snapshot должны регулярно сохраняться;
- если исторических данных мало, используется самый ранний доступный snapshot;
- показатели сотрудников не являются самостоятельной кадровой оценкой;
- задачи пока представлены агрегатами, без отдельных task nodes в knowledge graph;
- AI Coach не заменяет подтверждение владельцами процессов.

## Roadmap 1.0.0

- `alpha.1` — Unified Knowledge Graph и AI Provider Layer;
- `alpha.2` — динамика 7/30/90 дней;
- `alpha.3` — Process Mining MVP;
- `beta.1` — единый Executive Dashboard;
- `beta.2` — AI Coach, ROI и приоритизация;
- `1.0.0` — стабилизация, отчёт и документация.

## Правило разработки

1. изменения выполняются в ветке;
2. commit и push;
3. `git pull` на сервере;
4. пересборка контейнера;
5. smoke test;
6. merge после проверки.
