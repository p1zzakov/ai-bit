# AI-BIT

AI-BIT — read-only платформа для технического и функционального аудита коробочного Bitrix24.

Проект объединяет четыре слоя:

- **REST Collector** — пользователи, структура, CRM, задачи, группы и доступные бизнес-процессы;
- **Browser Worker** — интерфейсы, настройки и разделы, которых нет в REST;
- **Portal Crawler** — автоматическое обнаружение внутренних страниц и карта портала;
- **Implementation Assessment** — сравнение фактического внедрения с типовой целевой моделью Bitrix24.

Все операции против Bitrix24 выполняются в read-only режиме.

## Что уже реализовано

- браузерная авторизация и сохранение сессии;
- REST snapshot основных сущностей;
- scanner известных разделов;
- HTTP-, JavaScript- и network-диагностика;
- screenshot, HTML и evidence JSON;
- same-origin crawler;
- история crawl-запусков и diff;
- implementation score;
- матрица `используется / требует настройки / недоступно / не обнаружено`;
- рекомендации по сравнению с эталонной моделью;
- управленческий dashboard на `/dashboard`.

## Архитектура

```text
Bitrix24
   ├── REST API
   │      └── AI-BIT Backend :8080
   │             ├── snapshots
   │             ├── findings
   │             └── HTML report
   │
   └── Web UI
          └── Browser Worker :8090
                 ├── preset scanner
                 ├── portal crawler
                 ├── crawl history
                 ├── audit diff
                 ├── implementation assessment
                 ├── recommendation engine
                 └── web dashboard
```

## Структура проекта

```text
/opt/ai-bit/
├── app/                               # REST backend
├── browser-worker/
│   ├── app.py                         # базовый Browser Worker
│   ├── crawler.py                     # Portal Crawler
│   ├── history.py                     # история и diff
│   ├── implementation_analysis.py     # score и рекомендации
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

Текущая версия Browser Worker: `0.7.0`.

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
    "max_pages": 100,
    "max_depth": 3,
    "include_query": false,
    "save_html": false,
    "delay_ms": 300
  }' \
  -o /tmp/crawl.json
```

Crawler автоматически:

1. открывает портал под технической учётной записью;
2. извлекает внутренние ссылки;
3. исключает static, logout, download, ajax и REST URL;
4. классифицирует страницы по разделам;
5. сохраняет карту портала;
6. рассчитывает assessment;
7. сохраняет запуск в историю.

## Web Dashboard

Открыть:

```text
http://SERVER_IP:8090/dashboard
```

Dashboard показывает:

- implementation score;
- уровень зрелости внедрения;
- что уже используется;
- что требует настройки;
- что недоступно;
- что не обнаружено;
- матрицу модулей;
- приоритет рекомендаций;
- бизнес-ценность каждого действия;
- карту портала;
- все обнаруженные страницы;
- изменения между аудитами;
- нестандартные разделы и кастомные процессы.

## Логика assessment

AI-BIT сравнивает обнаруженные разделы с типовой целевой моделью:

- CRM;
- задачи и проекты;
- структура компании;
- цифровые процессы и формы;
- рабочие группы;
- документы и диск;
- календарь;
- база знаний;
- BI;
- почта;
- контакт-центр и открытые линии;
- RPA;
- маркетинг;
- интеграции и marketplace;
- инструменты разработчика;
- booking.

Для каждого модуля определяется состояние:

| Состояние | Значение |
|---|---|
| `used` | модуль обнаружен и доступен |
| `needs_configuration` | модуль есть, но требует настройки или подтверждения |
| `blocked` | модуль недоступен или возвращает ошибку доступа |
| `not_detected` | модуль не найден crawler-ом |

Implementation score рассчитывается эвристически с повышенным весом для критичных модулей: CRM, задачи, структура и цифровые процессы.

## Рекомендации

Recommendation Engine формирует рекомендации по трём уровням:

- `high` — критичный модуль отсутствует или заблокирован;
- `medium` — рекомендуемый модуль требует настройки;
- `low` — дополнительная возможность не используется.

Каждая рекомендация содержит:

- модуль;
- текущее состояние;
- действие;
- ожидаемую бизнес-ценность.

Оценка является экспертной эвристикой, а не официальным аудитом Bitrix24. Итоги должны подтверждаться владельцами процессов.

## API

### Авторизация

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/login?force=true' \
  -H 'Content-Type: application/json' \
  -d '{}' | jq
```

### Preset scanner

```bash
curl -sS http://127.0.0.1:8090/presets | jq
curl -sS -X POST http://127.0.0.1:8090/scan/all | jq
```

### История

```bash
curl -sS http://127.0.0.1:8090/crawl/history | jq
curl -sS http://127.0.0.1:8090/crawl/history/crawl-ID | jq
```

### Assessment

```bash
curl -sS http://127.0.0.1:8090/crawl/assessment/latest | jq
curl -sS http://127.0.0.1:8090/crawl/assessment/crawl-ID | jq
```

### Diff

```bash
curl -sS \
  'http://127.0.0.1:8090/crawl/diff?before=crawl-OLD&after=crawl-NEW' | jq
```

## Артефакты

```text
/app/artifacts/<timestamp>/
/app/artifacts/history/crawl-*.json
/app/artifacts/latest-crawl.json
```

При стандартном compose volume данные доступны на host в `/opt/ai-bit/reports/ui/`.

## Безопасность

- использовать отдельную техническую учётную запись;
- не публиковать порты 8080/8090 в интернет;
- ограничить доступ корпоративной сетью или VPN;
- не добавлять write scopes;
- перевыпускать временные webhook после discovery;
- не использовать личную учётную запись администратора.

## Ограничения

- crawler видит только ссылки с `href`;
- JavaScript-only меню пока не кликаются;
- `not_detected` не всегда означает, что модуль отсутствует;
- crawler пока не оценивает качество конкретной CRM-воронки или схемы бизнес-процесса;
- REST и browser evidence ещё не объединены в единый knowledge graph.

## Roadmap

- объединить REST snapshot и browser assessment;
- анализировать CRM-воронки, стадии, поля, роботов и триггеры;
- анализировать бизнес-процессы и маршруты согласования;
- аудит ролей и прав;
- интерактивный граф связей;
- управленческий PDF/Excel отчёт;
- AI-консультант по фактическим данным портала.

## Правило разработки

Все изменения выполняются через Git:

1. изменения в ветке;
2. commit и push;
3. `git pull` на сервере;
4. пересборка контейнера;
5. smoke test;
6. merge после проверки.
