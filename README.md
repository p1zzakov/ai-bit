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

Browser Worker: `1.0.0-rc.4`.

## Что добавлено в rc.4

### Enterprise UI Refresh

- полностью переработана Unified Enterprise Admin;
- добавлена постоянная боковая навигация;
- единая верхняя панель с названием текущего раздела;
- новый визуальный язык: градиенты, стеклянные поверхности, аккуратные тени и статусы;
- адаптивное отображение для широких экранов, планшетов и мобильных устройств;
- индикатор состояния системы в боковой панели;
- автоматическая проверка `/system/health` раз в минуту;
- кнопка обновления текущего раздела;
- кнопка открытия активного модуля в отдельной вкладке;
- экран загрузки при первом открытии и обновлении модуля;
- прямые hash-ссылки на каждый раздел сохранены.

Главная консоль:

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
#system
```

## System Health & Data Quality

- диагностика доступности Bitrix24;
- проверка REST webhook через `user.current`;
- проверка конфигурации Groq AI;
- контроль свежести crawl, operational snapshot, Process Mining и Business Architecture Audit;
- статусы `ok`, `warning`, `stale`, `missing`, `error`;
- отображение недоступных REST-источников и ошибок прав;
- рекомендации по обновлению устаревших контуров.

## Business Architecture Audit

### Business Process Audit

- шаблоны и активность бизнес-процессов;
- владельцы и описание назначения;
- активные, завершённые и проблемные экземпляры при наличии REST evidence;
- оценки `readiness`, `architecture`, `efficiency`, `automation`;
- рекомендации по SLA, владельцам, ошибкам и зависшим экземплярам.

### CRM Funnel Audit

- CRM-воронки и стадии;
- распределение сделок по стадиям;
- неиспользуемые стадии;
- сделки без ответственного, источника, суммы и следующей активности;
- оценки `readiness`, `architecture`, `data_quality`, `efficiency`, `automation`.

### Document Flow Audit

- документные бизнес-процессы;
- задачи по договорам, счетам, актам, заявкам и согласованиям;
- просрочка и задачи без срока;
- повторяющиеся документные операции;
- Browser evidence по страницам и формам;
- оценки `readiness`, `architecture`, `efficiency`, `automation`, `governance`.

## Архитектура

```text
AI-BIT Enterprise
├── Core
│   ├── Browser Worker
│   ├── REST Collector
│   ├── Portal Crawler
│   ├── Unified Knowledge Graph
│   └── AI Provider Layer / Groq
├── Enterprise Modules
│   ├── Implementation Audit
│   ├── Operational Intelligence
│   ├── Operational Trends
│   ├── Process Mining
│   ├── Business Process Audit
│   ├── CRM Funnel Audit
│   ├── Document Flow Audit
│   └── System Health & Data Quality
└── Interface
    └── Unified Enterprise Admin
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
  "version": "1.0.0-rc.4"
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
http://SERVER_IP:8090/system                 System Health & Data Quality
```

## System Health API

```bash
curl -sS http://127.0.0.1:8090/system/health | jq
```

Краткая сводка:

```bash
curl -sS http://127.0.0.1:8090/system/health \
  | jq '{overall_status,summary,data_quality}'
```

## Сбор данных

```bash
curl -sS -X POST http://127.0.0.1:8090/operations/collect -o /tmp/operations.json
curl -sS -X POST http://127.0.0.1:8090/business-architecture/collect -o /tmp/business-architecture.json
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

## Ограничения rc.4

- внутренние панели пока загружаются в iframe внутри единой оболочки;
- визуальный стиль вложенных модулей частично сохраняет предыдущую тему;
- проверка Groq подтверждает конфигурацию ключа, но не расходует токены на тестовый completion;
- часть методов бизнес-процессов зависит от редакции Bitrix24 и прав webhook;
- свежесть отражает время последнего snapshot, а не полноту данных внутри него;
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
