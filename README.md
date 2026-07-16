# AI-BIT

AI-BIT — read-only платформа для технического и функционального аудита коробочного Bitrix24.

Проект объединяет:

- **REST Collector** — массовая выгрузка пользователей, структуры, CRM, задач, групп и доступных бизнес-процессов;
- **Browser Worker** — авторизованный просмотр интерфейсов, настроек и разделов, которых нет в REST;
- **Portal Crawler** — автоматическое обнаружение same-origin страниц и построение карты портала;
- **Audit History & Diff** — хранение запусков и сравнение изменений;
- **Web Dashboard** — визуализация карты портала, KPI, статусов и изменений.

Все операции против Bitrix24 выполняются в read-only режиме.

## Текущий статус

Реализовано:

- браузерная авторизация и сохранение сессии;
- REST snapshot основных сущностей;
- сканирование известных разделов по пресетам;
- HTTP-, JavaScript- и network-диагностика;
- screenshot, HTML и evidence JSON;
- статусы `ok`, `redirected`, `partial`, `denied`, `not_found`, `error`;
- scorecard покрытия известных разделов;
- same-origin crawler с глубиной и лимитом страниц;
- история crawl-запусков;
- diff добавленных, удалённых и изменённых страниц;
- веб-панель на `/dashboard`;
- отсутствие write-операций против Bitrix24.

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
                 ├── web dashboard
                 └── evidence artifacts
```

## Структура проекта

```text
/opt/ai-bit/
├── app/                            # основной REST backend
├── browser-worker/
│   ├── app.py                      # базовый Browser Worker
│   ├── build_patch.py              # scanner/readiness расширения
│   ├── crawler.py                  # Portal Crawler
│   ├── crawler_patch.py            # crawler API endpoints
│   ├── history.py                  # история и diff
│   ├── dashboard.py                # HTML dashboard
│   ├── history_patch.py            # dashboard/history API endpoints
│   ├── login_debug.py              # диагностика входа
│   ├── presets.json                # известные разделы и readiness selectors
│   └── Dockerfile
├── reports/                        # snapshots и browser artifacts
├── docker-compose.yml
├── .env                            # секреты, не коммитить
└── .env.example
```

## Требования

Рекомендуемая VM:

- Ubuntu Server 24.04 LTS;
- 4 vCPU;
- 8 GB RAM;
- 80–100 GB disk;
- HTTPS-доступ к Bitrix24;
- Docker Engine и Docker Compose v2.

## Конфигурация

Создайте `.env` на основе `.env.example`.

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

Никогда не коммитьте `.env`, webhook URL, пароли, токены или browser storage state.

## Установка и обновление

```bash
cd /opt/ai-bit
git pull
docker compose build --no-cache
docker compose up -d
```

Проверка:

```bash
docker compose ps
curl -sS http://127.0.0.1:8080/health | jq
curl -sS http://127.0.0.1:8090/health | jq
```

## Web Dashboard

После запуска Browser Worker откройте:

```text
http://SERVER_IP:8090/dashboard
```

Dashboard показывает:

- количество посещённых и обнаруженных страниц;
- распределение по разделам;
- карту портала;
- список страниц и их статусы;
- историю crawl-аудитов;
- добавленные, удалённые и изменённые страницы относительно предыдущего запуска.

Первый crawl создаёт базовую точку. Diff появится после второго запуска.

## Browser Worker API

### Авторизация

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/login?force=true' \
  -H 'Content-Type: application/json' \
  -d '{}' | jq
```

### Известные пресеты

```bash
curl -sS http://127.0.0.1:8090/presets | jq
```

### Сканирование одного раздела

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/scan/preset/crm | jq
```

### Полное сканирование пресетов

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/scan/all \
  -o /tmp/scan-all.json

jq '{status,summary,errors}' /tmp/scan-all.json
```

## Portal Crawler

Crawler открывает портал, извлекает внутренние ссылки, нормализует URL, исключает logout/download/ajax/static ресурсы и формирует карту same-origin страниц.

Пример запуска:

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

Результат:

```bash
jq '{history_id,summary,errors,artifact}' /tmp/crawl.json
jq '.nodes[] | {depth,section,title,status,url}' /tmp/crawl.json
```

Последний crawl:

```bash
curl -sS http://127.0.0.1:8090/crawl/latest | jq
```

## История и сравнение аудитов

Список запусков:

```bash
curl -sS http://127.0.0.1:8090/crawl/history | jq
```

Получение конкретного запуска:

```bash
curl -sS \
  http://127.0.0.1:8090/crawl/history/crawl-YYYYMMDDTHHMMSSZ | jq
```

Сравнение двух запусков:

```bash
curl -sS \
  'http://127.0.0.1:8090/crawl/diff?before=crawl-OLD&after=crawl-NEW' | jq
```

Diff включает:

- новые URL;
- удалённые URL;
- изменения `title`, `status`, `section`, `http_status`;
- изменение количества страниц по разделам.

История сохраняется в:

```text
/app/artifacts/history/crawl-*.json
```

При стандартном `docker-compose.yml` этот каталог должен находиться на persistent host volume.

## REST-аудит

Capability explorer:

```bash
curl -sS -X POST http://127.0.0.1:8080/api/v1/explorer/run | jq
```

Полный REST-аудит:

```bash
curl -sS -X POST http://127.0.0.1:8080/api/v1/audits/run | jq
```

HTML-отчёт:

```text
http://SERVER_IP:8080/api/v1/reports/latest
```

## Статусы страниц

| Статус | Значение |
|---|---|
| `ok` | страница открыта и распознана |
| `redirected` | Bitrix перенаправил на фактический URL |
| `partial` | страница открыта, но readiness/контент подтверждены частично |
| `denied` | HTTP 401/403 или отказ доступа |
| `not_found` | HTTP 404 |
| `error` | ошибка навигации или Playwright |

`partial` не всегда означает неисправность Bitrix24. Причиной может быть отличающийся DOM, lazy loading или необязательный frontend-ресурс.

## Артефакты

Browser Worker сохраняет:

- screenshot;
- HTML;
- evidence JSON;
- crawl site map;
- историю crawl;
- HTTP status и итоговый URL;
- console/page errors;
- failed requests и HTTP 4xx/5xx;
- readiness selector.

Host volume обычно доступен в:

```text
/opt/ai-bit/reports/ui/
```

## Безопасность

- Используйте отдельную техническую учётную запись.
- Не используйте личную учётную запись администратора.
- Ограничьте доступ к портам 8080 и 8090 корпоративной сетью или VPN.
- Не публикуйте Browser Worker напрямую в интернет.
- После REST discovery перевыпускайте временный webhook.
- Не добавляйте write scopes без отдельного согласования.
- Перед crawl убедитесь, что пароль не истёк и нет обязательного 2FA challenge.

## Известные ограничения

- REST API не показывает все визуальные настройки и схемы автоматизации.
- Browser Worker зависит от версии интерфейса коробочного Bitrix24.
- Crawler не нажимает JavaScript-only элементы без `href`.
- Crawler не выполняет формы, POST-запросы и write-действия.
- Динамические пользовательские URL могут создавать шум; требуется дальнейшая дедупликация.
- Карта портала — техническое обнаружение, а не окончательная оценка качества внедрения.

## Roadmap

Ближайшие этапы:

- дедупликация динамических URL и технических страниц;
- интерактивный граф связей вместо только древовидного списка;
- фильтры по разделам, статусам и глубине;
- объединение REST snapshot и browser evidence;
- implementation score по CRM, задачам, HR, процессам и интеграциям;
- аудит CRM-воронок, стадий, полей, роботов и триггеров;
- анализ бизнес-процессов и маршрутов согласования;
- аудит ролей, приложений и интеграций;
- управленческий HTML/PDF/Excel отчёт;
- AI-консультант по данным портала.

## Правило разработки

Все изменения выполняются через Git:

1. изменение исходников в ветке;
2. commit и push;
3. `git pull` на сервере;
4. пересборка контейнера;
5. проверка health и функционального endpoint.

Ручное редактирование файлов внутри работающего контейнера не используется.
