# AI-BIT

AI-BIT — read-only платформа технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `1.0.0-beta.2`.

## Что добавлено в beta.2

- Process Mining MVP;
- компактные task events в operational snapshot;
- группировка повторяющихся задач по нормализованному названию;
- кандидаты на шаблоны задач и бизнес-процессы;
- повторяющиеся маршруты `постановщик → исполнитель`;
- выявление потенциальных ручных диспетчерских узлов;
- automation score для приоритизации;
- ориентировочная оценка ручного времени;
- отдельный Process Mining Dashboard;
- передача выводов Process Mining в Groq AI Coach.

Все операции против Bitrix24 выполняются в read-only режиме.

## Архитектура

AI-BIT объединяет:

- REST Collector;
- Browser Worker и Portal Crawler;
- Deep Audit;
- Operational Intelligence;
- Operational Trends 7/30/90;
- Process Mining;
- Unified Knowledge Graph;
- AI Provider Layer на Groq;
- Executive Dashboard.

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
  "version": "1.0.0-beta.2"
}
```

## Интерфейсы

```text
http://SERVER_IP:8090/           Executive Dashboard и AI Coach
http://SERVER_IP:8090/executive  Executive Dashboard и AI Coach
http://SERVER_IP:8090/dashboard  Аудит внедрения
http://SERVER_IP:8090/operations Operational Intelligence
http://SERVER_IP:8090/processes  Process Mining
```

## Сбор данных

После обновления обязательно собрать новый snapshot: старые snapshot не содержат `task_events`.

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/operations/collect \
  -o /tmp/operations-beta2.json
```

Проверка:

```bash
jq '{summary, process_mining_summary}' /tmp/operations-beta2.json
```

## Process Mining API

```bash
curl -sS \
  http://127.0.0.1:8090/process-mining/latest \
  | jq
```

Краткая сводка:

```bash
curl -sS \
  http://127.0.0.1:8090/process-mining/latest \
  | jq '.summary'
```

Кандидаты на автоматизацию:

```bash
curl -sS \
  http://127.0.0.1:8090/process-mining/latest \
  | jq '.automation_candidates[] | {
      sample_title,
      count,
      overdue,
      without_deadline,
      automation_score,
      estimated_manual_minutes,
      recommendation
    }'
```

Повторяющиеся маршруты:

```bash
curl -sS \
  http://127.0.0.1:8090/process-mining/latest \
  | jq '.handoff_routes'
```

Потенциальные узкие места:

```bash
curl -sS \
  http://127.0.0.1:8090/process-mining/latest \
  | jq '.bottlenecks'
```

## Как считается Process Mining MVP

- названия задач приводятся к нижнему регистру;
- из названий удаляются URL, номера и служебные слова;
- одинаковые нормализованные названия группируются;
- паттерн с тремя и более задачами считается повторяющимся;
- отдельно анализируются устойчивые пары постановщик → исполнитель;
- automation score повышается при высокой частоте, просрочке и задачах без срока;
- оценка ручного времени использует базовое допущение: 5 минут на повторяющуюся операцию.

Оценка времени не является подтверждённым ROI. Перед внедрением владелец процесса должен подтвердить частоту, сложность и стоимость ручной операции.

## Groq AI Coach

AI Coach доступен на `/executive`. Он получает:

- audit evidence;
- operational summary;
- тренды;
- кандидатов на автоматизацию;
- повторяющиеся маршруты;
- потенциальные узкие места.

Примеры вопросов:

```text
Какие повторяющиеся задачи стоит автоматизировать первыми?
Какие маршруты постановщик → исполнитель похожи на ручную диспетчеризацию?
Сформируй план автоматизации на 30 дней.
Какие кандидаты дадут максимальную экономию времени?
```

## Основные API

```text
GET  /
GET  /executive
GET  /dashboard
GET  /operations
GET  /processes
GET  /health
POST /login
POST /crawl
GET  /crawl/history
GET  /crawl/assessment/latest
GET  /crawl/deep-audit/latest
GET  /crawl/diff
POST /operations/collect
GET  /operations/latest
GET  /operations/history
GET  /operations/trends?days=7|30|90
GET  /process-mining/latest
GET  /knowledge-graph/latest
GET  /ai/status
POST /ai/advice
```

## Ограничения beta.2

- качество Process Mining зависит от дисциплины наименования задач;
- одинаковое название не гарантирует одинаковый бизнес-процесс;
- задачи из старых snapshot не участвуют в анализе;
- оценка времени ориентировочная и не является финансовым эффектом;
- показатели сотрудников не являются самостоятельной кадровой оценкой;
- перед передачей персональных данных во внешний AI требуется корпоративная политика.

## Roadmap 1.0.0

- `alpha.1` — Unified Knowledge Graph и AI Provider Layer;
- `alpha.2` — динамика 7/30/90 дней;
- `alpha.3` — Process Mining MVP, реализован в составе beta.2;
- `beta.1` — Executive Dashboard и встроенный AI Coach;
- `beta.2` — Process Mining, первичная оценка эффекта и расширенный AI Coach;
- `1.0.0` — стабилизация, управленческий отчёт и документация.

## Правило разработки

1. изменения выполняются в ветке;
2. commit и push;
3. `git pull` на сервере;
4. пересборка контейнера;
5. smoke test;
6. merge после проверки.
