# AI-BIT

AI-BIT — read-only платформа для технического, функционального и управленческого аудита коробочного Bitrix24.

Текущая версия Browser Worker: **0.8.0**.

## Архитектура

AI-BIT объединяет пять слоёв:

- **REST Collector** — пользователи, структура, CRM, задачи, группы и бизнес-процессы;
- **Browser Worker** — интерфейсы и настройки, которых нет в REST;
- **Portal Crawler** — обнаружение внутренних страниц и построение карты портала;
- **Implementation Assessment** — оценка покрытия типовой целевой модели Bitrix24;
- **Deep Audit Engine** — рекомендации по модулям и каждой обнаруженной странице.

Все операции против Bitrix24 выполняются в read-only режиме.

## Возможности 0.8.0

- браузерная авторизация и сохранение сессии;
- scanner известных разделов;
- same-origin crawler с контрольными стартовыми маршрутами;
- HTTP-, JavaScript- и network-диагностика;
- screenshot, HTML и evidence JSON;
- история crawl-запусков и diff;
- implementation score;
- матрица `used / needs_configuration / blocked / not_detected`;
- глубокий аудит CRM, задач, структуры, цифровых процессов, рабочих групп, диска, календаря, базы знаний и RPA;
- рекомендации по каждому модулю;
- рекомендации по каждой обнаруженной странице;
- приоритетный план действий;
- новый dashboard на `/dashboard`.

## Структура проекта

```text
/opt/ai-bit/
├── app/                               # REST backend
├── browser-worker/
│   ├── app.py                         # базовый Browser Worker
│   ├── crawler.py                     # Portal Crawler
│   ├── history.py                     # история и diff
│   ├── implementation_analysis.py     # implementation score
│   ├── deep_audit.py                  # Deep Audit Engine 0.8.0
│   ├── dashboard.py                   # HTML dashboard
│   ├── presets.json                   # известные разделы
│   ├── build_patch.py
│   ├── crawler_patch.py
│   ├── history_patch.py
│   └── Dockerfile
├── reports/
├── docker-compose.yml
├── .env
└── .env.example
```

## Развёртывание

```bash
cd /opt/ai-bit

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
  "version": "0.8.0"
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

Не коммитьте `.env`, webhook URL, пароли, токены и browser storage state.

## Запуск crawler

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

Crawler автоматически:

1. открывает портал под технической учётной записью;
2. запускает обход с главной страницы и контрольных разделов Bitrix24;
3. извлекает внутренние ссылки;
4. исключает static, logout, download, ajax и REST URL;
5. классифицирует страницы по разделам;
6. сохраняет карту портала;
7. рассчитывает implementation assessment;
8. рассчитывает deep audit;
9. сохраняет запуск в историю.

## Dashboard

```text
http://SERVER_IP:8090/dashboard
```

Вкладки dashboard:

- **Обзор** — implementation score и текущее покрытие;
- **Глубокий аудит модулей** — цель модуля, контрольные точки, состояние и рекомендации;
- **Аудит страниц** — риск, evidence и рекомендации по каждой странице;
- **План действий** — приоритетные изменения и ожидаемый эффект;
- **Карта портала** — дерево и список обнаруженных страниц;
- **Изменения** — diff между crawl-запусками.

## API

### Авторизация

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/login?force=true' \
  -H 'Content-Type: application/json' \
  -d '{}' | jq
```

### История

```bash
curl -sS http://127.0.0.1:8090/crawl/history | jq
curl -sS http://127.0.0.1:8090/crawl/history/crawl-ID | jq
```

### Implementation Assessment

```bash
curl -sS http://127.0.0.1:8090/crawl/assessment/latest | jq
curl -sS http://127.0.0.1:8090/crawl/assessment/crawl-ID | jq
```

### Deep Audit 0.8.0

```bash
curl -sS http://127.0.0.1:8090/crawl/deep-audit/latest | jq
curl -sS http://127.0.0.1:8090/crawl/deep-audit/crawl-ID | jq
```

Краткая сводка:

```bash
curl -sS http://127.0.0.1:8090/crawl/deep-audit/latest \
  | jq '{version, summary, action_plan}'
```

### Diff

```bash
curl -sS \
  'http://127.0.0.1:8090/crawl/diff?before=crawl-OLD&after=crawl-NEW' | jq
```

## Методика Deep Audit

Версия 0.8.0 использует browser evidence:

- URL и раздел;
- заголовок;
- HTTP и функциональный статус;
- глубину страницы;
- количество ссылок;
- видимый текст;
- наличие признаков SLA, ответственного, статусов и этапов.

На основе этих данных движок формирует:

- состояние модуля;
- перечень контрольных точек;
- рекомендации по оптимизации;
- рекомендации по каждой странице;
- приоритетный план действий.

Это экспертная эвристика. Она не заменяет интервью с владельцами процессов и пока не анализирует внутренние настройки CRM, роботов и фактические показатели задач.

## Ограничения 0.8.0

- crawler видит в основном страницы и ссылки, доступные технической учётной записи;
- JavaScript-only сценарии могут требовать отдельных preset-проверок;
- рекомендации по страницам строятся по browser evidence;
- воронки, стадии, поля, роботы, триггеры и задачи требуют REST-аналитики;
- пользовательская эффективность не рассчитывается до версии 0.9.0;
- `not_detected` не всегда означает физическое отсутствие модуля.

## Roadmap до 1.0.0

### 0.8.0 — Deep Audit

- глубокий аудит модулей;
- рекомендации по каждой странице;
- контрольные точки по CRM, задачам и процессам;
- план действий с приоритетами;
- evidence-based dashboard.

### 0.9.0 — Operational Intelligence

- аналитика пользователей;
- аналитика подразделений;
- открытые, завершённые и просроченные задачи;
- задачи без срока и результата;
- нагрузка и риск перегрузки;
- тренды за 7/30/90 дней;
- CRM-дисциплина и зависшие сделки;
- управленческий dashboard.

### 1.0.0 — AI Management Advisor

- единый REST + Browser knowledge graph;
- process mining;
- Executive Dashboard;
- AI Coach: почему плохо, как исправить и какой эффект;
- оценка ROI автоматизации;
- план цифровой трансформации;
- управленческий PDF/Excel отчёт;
- непрерывный аудит и динамика зрелости.

## Безопасность

- использовать отдельную техническую учётную запись;
- не публиковать порты 8080/8090 в интернет;
- ограничить доступ корпоративной сетью или VPN;
- не добавлять write scopes;
- не использовать личную учётную запись администратора;
- не коммитить секреты и browser storage state.

## Правило разработки

Все изменения выполняются через Git:

1. изменения в feature-ветке;
2. commit и push;
3. `git pull` на сервере;
4. пересборка контейнера;
5. smoke test;
6. merge после проверки.
