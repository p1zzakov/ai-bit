# AI-BIT

AI-BIT — read-only платформа технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `1.0.0-beta.1`.

## Что добавлено в beta.1

- единый Executive Dashboard;
- главная страница `/` и отдельный маршрут `/executive`;
- сводка зрелости внедрения, задач, просрочки, риска и 30-дневного тренда;
- блок главных управленческих рисков;
- блок приоритетных действий;
- встроенный AI Coach на Groq прямо в браузере;
- быстрые запросы: главные риски, план на 30 дней, кандидаты на автоматизацию;
- произвольный вопрос к Groq без использования `curl`;
- ответы AI формируются по текущему crawl, Operational Intelligence и трендам.

## Архитектура

AI-BIT объединяет:

- REST Collector;
- Browser Worker;
- Portal Crawler;
- Deep Audit;
- Operational Intelligence;
- Operational Trends 7/30/90;
- Unified Knowledge Graph;
- AI Provider Layer;
- Executive Dashboard.

Все операции против Bitrix24 выполняются в read-only режиме.

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
  "version": "1.0.0-beta.1"
}
```

## Интерфейсы

Executive Dashboard и AI Coach:

```text
http://SERVER_IP:8090/
http://SERVER_IP:8090/executive
```

Аудит внедрения:

```text
http://SERVER_IP:8090/dashboard
```

Operational Intelligence:

```text
http://SERVER_IP:8090/operations
```

### Как задавать вопросы Groq

1. открыть `/executive`;
2. в блоке **AI Coach · Groq** ввести вопрос;
3. нажать **Спросить Groq**;
4. для отправки с клавиатуры использовать `Ctrl+Enter`.

Примеры вопросов:

```text
Почему 20% задач просрочены и что изменить в процессе?
Какие подразделения требуют внимания в первую очередь?
Какие процессы стоит автоматизировать?
Сформируй план улучшений на ближайшие 30 дней.
```

## Operational Intelligence API

Собрать snapshot:

```bash
curl -sS -X POST http://127.0.0.1:8090/operations/collect | jq '.summary'
```

Последний snapshot:

```bash
curl -sS http://127.0.0.1:8090/operations/latest | jq '.summary'
```

Тренды:

```bash
curl -sS 'http://127.0.0.1:8090/operations/trends?days=7' | jq
curl -sS 'http://127.0.0.1:8090/operations/trends?days=30' | jq
curl -sS 'http://127.0.0.1:8090/operations/trends?days=90' | jq
```

## AI API

Статус:

```bash
curl -sS http://127.0.0.1:8090/ai/status | jq
```

Запрос из CLI:

```bash
curl -sS -X POST \
  --get \
  --data-urlencode 'question=Сформируй приоритетный план улучшений' \
  http://127.0.0.1:8090/ai/advice \
  | jq
```

Интеграция использует официальный Python SDK `groq`. В AI передаются агрегированные показатели, тренды, рекомендации и audit evidence.

## Основные API

```text
GET  /
GET  /executive
GET  /dashboard
GET  /operations
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
GET  /knowledge-graph/latest
GET  /ai/status
POST /ai/advice
```

## Ограничения beta.1

- тренды требуют регулярного накопления snapshot;
- AI работает по агрегированным данным и не заменяет владельцев процессов;
- показатели сотрудников не являются самостоятельной кадровой оценкой;
- Process Mining MVP и ROI автоматизации будут добавлены следующими патчами;
- перед передачей персональных данных во внешний AI требуется корпоративная политика.

## Roadmap 1.0.0

- `alpha.1` — Unified Knowledge Graph и AI Provider Layer;
- `alpha.2` — динамика 7/30/90 дней;
- `alpha.3` — Process Mining MVP;
- `beta.1` — Executive Dashboard и встроенный AI Coach;
- `beta.2` — ROI, расширенная приоритизация и AI Coach;
- `1.0.0` — стабилизация, отчёт и документация.

## Правило разработки

1. изменения выполняются в ветке;
2. commit и push;
3. `git pull` на сервере;
4. пересборка контейнера;
5. smoke test;
6. merge после проверки.
