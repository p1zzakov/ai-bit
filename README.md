# AI-BIT

AI-BIT — read-only платформа технического, функционального и операционного аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `1.0.0-alpha.1`.

## Архитектура

AI-BIT объединяет семь контуров:

- **REST Collector** — пользователи, подразделения, задачи, CRM и другие сущности;
- **Browser Worker** — UI-разделы и настройки, которых нет в REST;
- **Portal Crawler** — карта внутренних страниц;
- **Deep Audit** — рекомендации по модулям и страницам;
- **Operational Intelligence** — нагрузка, просрочка и риски подразделений;
- **Unified Knowledge Graph** — связь пользователей, подразделений, модулей, страниц и рекомендаций;
- **AI Provider Layer** — экспертные рекомендации через Groq с возможностью смены провайдера.

Все операции против Bitrix24 выполняются в read-only режиме.

## Возможности 1.0.0-alpha.1

- объединение последнего crawl и operational snapshot в единый knowledge graph;
- узлы: модули, страницы, пользователи, подразделения, рекомендации;
- связи: принадлежность страниц модулям и сотрудников подразделениям;
- единый API для последующего Executive Dashboard и Process Mining;
- AI status endpoint;
- AI Coach MVP через Groq API;
- официальный Python SDK `groq` для запросов к GroqCloud;
- передача в AI только агрегированного контекста и evidence;
- защита от выдуманных данных через системное требование работать только по фактам.

## Почему Groq

Groq используется как основной inference-провайдер из-за высокой скорости ответа и OpenAI-совместимого API. Архитектура не привязана к одному поставщику: провайдер и модель задаются переменными окружения.

Интеграция использует официальный Python SDK `groq`. Прямые запросы через стандартный `urllib` не используются, так как защитный контур API может блокировать такие клиенты кодом Cloudflare `1010`.

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
  "version": "1.0.0-alpha.1"
}
```

## Dashboard

```text
http://SERVER_IP:8090/dashboard
http://SERVER_IP:8090/operations
```

## Unified Knowledge Graph API

```bash
curl -sS http://127.0.0.1:8090/knowledge-graph/latest | jq
```

Краткая сводка:

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

Получить управленческую рекомендацию:

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/ai/advice?question=Сформируй%20приоритетный%20план%20улучшения%20внедрения%20Bitrix24' \
  | jq
```

AI получает компактный контекст: сводку knowledge graph, фактические рекомендации, operational summary, implementation assessment и deep audit summary.

### Диагностика Groq

Проверить, что ключ попал внутрь контейнера:

```bash
docker compose exec browser-worker sh -lc 'test -n "$GROQ_API_KEY" && echo GROQ_API_KEY=SET || echo GROQ_API_KEY=EMPTY'
```

Проверить установленный SDK:

```bash
docker compose exec browser-worker python -c 'import groq; print(groq.__version__)'
```

Если после перехода на официальный SDK остаётся HTTP 403, проверить доступ сервера к GroqCloud с другого внешнего IP: блокировка может быть связана с политикой аккаунта, региона или исходного адреса.

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
GET  /knowledge-graph/latest
GET  /ai/status
POST /ai/advice
```

## Ограничения alpha.1

- knowledge graph пока объединяет последние доступные snapshots;
- задачи представлены агрегатами сотрудников, без отдельных task nodes;
- AI Coach не заменяет подтверждение владельцами процессов;
- перед отправкой чувствительных данных во внешний AI необходимо утвердить корпоративную политику;
- Groq API key хранится только в `.env` на сервере;
- история трендов, Process Mining и Executive Dashboard будут добавлены следующими alpha/beta-патчами.

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
