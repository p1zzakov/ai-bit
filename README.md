# AI-BIT

AI-BIT — read-only платформа для технического и функционального аудита коробочного Bitrix24.

Проект объединяет два источника данных:

1. **Bitrix24 REST API** — массовая выгрузка пользователей, подразделений, CRM, задач, групп, полей и доступных бизнес-процессов.
2. **Browser Worker на Playwright** — просмотр интерфейсов и настроек, которые REST API не отдаёт или отдаёт неполно.

Цель проекта — определить фактическое состояние внедрения Bitrix24, обнаружить недоступные, неиспользуемые и частично настроенные модули, сохранить доказательства и подготовить данные для итогового отчёта руководству.

## Текущий статус

MVP работает в read-only режиме.

Реализовано:

- авторизация в коробочном Bitrix24 через браузер;
- сохранение браузерной сессии;
- REST-снимок основных сущностей;
- сканирование ключевых разделов портала;
- конфигурируемые browser-пресеты;
- HTTP-, JS- и сетевые диагностические данные;
- сохранение HTML, screenshot и evidence JSON;
- классификация страниц: `ok`, `redirected`, `partial`, `denied`, `not_found`, `error`;
- scorecard покрытия портала;
- автоматический same-origin crawler для построения карты Bitrix24;
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
                 ├── presets scan
                 ├── crawler
                 ├── screenshots
                 ├── HTML evidence
                 └── network diagnostics
```

## Каталоги проекта

```text
/opt/ai-bit/
├── app/                         # основной FastAPI backend
├── browser-worker/
│   ├── app.py                   # базовый browser worker
│   ├── build_patch.py           # build-time расширения scanner 0.4
│   ├── crawler.py               # автоматический crawler портала
│   ├── crawler_patch.py         # подключение crawler API
│   ├── login_debug.py           # диагностика авторизации
│   ├── presets.json             # конфигурация известных разделов
│   └── Dockerfile
├── reports/                     # REST-отчёты и browser evidence
├── docker-compose.yml
├── .env                         # секреты, не коммитить
└── .env.example
```

## Требования

Рекомендуемая VM:

- Ubuntu Server 24.04 LTS;
- 4 vCPU;
- 8 GB RAM;
- 80–100 GB disk;
- доступ по HTTPS к Bitrix24;
- Docker Engine и Docker Compose v2.

## Конфигурация

Создать `.env` на основе `.env.example`.

Ключевые параметры:

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

Не добавляйте `.env`, webhook URL, пароль, токены и browser storage state в Git.

## Установка и обновление

```bash
cd /opt/ai-bit
git pull
docker compose build --no-cache
docker compose up -d
```

Проверка контейнеров:

```bash
docker compose ps
curl -sS http://127.0.0.1:8080/health | jq
curl -sS http://127.0.0.1:8090/health | jq
```

## REST-аудит

Запуск capability explorer:

```bash
curl -sS -X POST http://127.0.0.1:8080/api/v1/explorer/run | jq
```

Запуск полного REST-аудита:

```bash
curl -sS -X POST http://127.0.0.1:8080/api/v1/audits/run | jq
```

Последний HTML-отчёт:

```text
http://SERVER_IP:8080/api/v1/reports/latest
```

Основные JSON endpoints:

```text
GET /api/v1/explorer/latest
GET /api/v1/reports/latest/summary
GET /api/v1/reports/latest/findings
```

## Browser Worker

### Авторизация

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/login?force=true' \
  -H 'Content-Type: application/json' \
  -d '{}' | jq
```

Проверка сохранённой сессии:

```bash
curl -sS http://127.0.0.1:8090/health | jq
```

### Пресеты

Пресеты находятся в `browser-worker/presets.json`.

```bash
curl -sS http://127.0.0.1:8090/presets | jq
```

Пример preset:

```json
{
  "crm": {
    "path": "/crm/",
    "wait_for": [
      ".crm-kanban",
      ".main-grid",
      "#workarea-content"
    ],
    "critical": true
  }
}
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

## AI Crawler

Crawler автоматически открывает портал, извлекает внутренние ссылки, нормализует URL, исключает logout/download/ajax/static ресурсы и строит карту same-origin страниц.

Ограничения по умолчанию:

- максимум 50 страниц;
- глубина обхода 2;
- query string не учитывается;
- задержка между страницами 250 ms;
- write-действия не выполняются.

### Запуск crawler

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/crawl \
  -H 'Content-Type: application/json' \
  -d '{
    "start_path": "/",
    "max_pages": 50,
    "max_depth": 2,
    "include_query": false,
    "save_html": false,
    "delay_ms": 250
  }' \
  -o /tmp/crawl.json
```

Краткий результат:

```bash
jq '{summary,errors,artifact}' /tmp/crawl.json
```

Список обнаруженных разделов:

```bash
jq '.nodes[] | {section,title,status,url}' /tmp/crawl.json
```

Последний crawl:

```bash
curl -sS http://127.0.0.1:8090/crawl/latest | jq
```

Результат сохраняется в:

```text
/app/artifacts/<timestamp>/crawl/site-map.json
/app/artifacts/latest-crawl.json
```

## Статусы страниц

| Статус | Значение |
|---|---|
| `ok` | URL открыт, страница распознана |
| `redirected` | Bitrix перенаправил на фактический раздел |
| `partial` | страница открыта, но часть интерфейса или readiness selector не подтверждены |
| `denied` | HTTP 401/403 или отказ доступа |
| `not_found` | HTTP 404 |
| `error` | ошибка навигации или Playwright |

`partial` не всегда означает неисправность Bitrix24. Причиной может быть другая версия DOM, ленивый frontend-компонент или необязательный JS-ресурс.

## Артефакты

Browser Worker сохраняет:

- screenshot;
- HTML страницы;
- evidence JSON;
- итоговый URL;
- HTTP status;
- console warnings/errors;
- page errors;
- failed requests;
- HTTP 4xx/5xx;
- readiness selector;
- crawl site map.

На сервере host volume обычно доступен в:

```text
/opt/ai-bit/reports/ui/
```

## Безопасность

- Система предназначена для read-only аудита.
- Используйте отдельную техническую учётную запись.
- Не используйте личную учётную запись администратора.
- После первичного REST discovery перевыпустите временный webhook.
- Ограничьте доступ к портам 8080 и 8090 корпоративной сетью или VPN.
- Не публикуйте Browser Worker напрямую в интернет.
- Не добавляйте write REST scopes без отдельного согласования.
- Перед crawl убедитесь, что учётная запись не имеет обязательной смены пароля или 2FA challenge.

## Известные ограничения

- REST API не показывает все визуальные настройки, права и схемы автоматизации.
- Browser Worker зависит от фактической версии интерфейса коробочного Bitrix24.
- Некоторые страницы используют slider, iframe и ленивую загрузку.
- Crawler пока не нажимает элементы меню, открываемые только через JavaScript без `href`.
- Crawler не выполняет формы, POST-запросы и write-действия.
- Карта портала — техническое обнаружение страниц, а не окончательная оценка качества внедрения.

## Roadmap

### Ближайший этап

- классификация обнаруженных crawler URL по модулям;
- дедупликация динамических Bitrix URL;
- карта меню и вложенности портала;
- отдельные discovery-профили для CRM, задач, HR, RPA и бизнес-процессов;
- объединение REST snapshot и browser evidence;
- автоматический implementation score;
- отчёт «что внедрено / что отсутствует / что требует доработки».

### Следующий этап

- аудит CRM-воронок, стадий и полей;
- анализ роботов и триггеров;
- анализ бизнес-процессов и маршрутов согласования;
- аудит ролей и прав;
- аудит приложений и интеграций;
- история запусков и сравнение изменений;
- генерация управленческого HTML/PDF/Excel отчёта;
- AI-консультант по данным портала.

### Перспектива

Модульная платформа аудита корпоративной инфраструктуры:

```text
Bitrix24
AD / LDAP
Kerio Connect
VMware
MikroTik
Zabbix
1C
```

## Принцип разработки

Все изменения выполняются через Git. Контейнеры не патчатся вручную.

Рабочий цикл:

```text
Git commit → git pull → docker build → docker compose up → проверка API
```

Это обеспечивает повторяемость, контроль изменений и возможность отката.
