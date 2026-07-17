# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.5`.

## 2.0.0-alpha.5 — Knowledge Base & Methodology

AI-BIT получил отдельную базу знаний по зрелому внедрению Bitrix24. Методика больше не хранится только в промптах и условиях кода.

Для каждого направления база знаний содержит:

- целевое состояние;
- лучшие практики;
- типовые анти-паттерны;
- требования к доказательствам;
- рекомендации для статусов `missing`, `partial` и `implemented`;
- версию методики и дисклеймер.

Первый набор знаний покрывает:

- задачи и поручения;
- CRM и продажи;
- бизнес-процессы;
- согласование договоров;
- электронный обмен документами;
- служебные записки;
- создание пользователей и доступов;
- базу знаний и регламенты.

Reference Model Audit автоматически обогащает каждый результат методическими данными. На странице `#management` для выявленных разрывов показывается рекомендация по методике AI-BIT, а не свободная формулировка из промпта.

Методика AI-BIT является экспертной моделью и не является официальной сертификацией 1С-Битрикс.

## Главная ссылка для руководства

```text
http://SERVER_IP:8090/#management
```

Ссылка не меняется. Страница показывает только системно обнаруженные факты, доказательства, уверенность и рекомендации из базы знаний.

## Основные модули

- Implementation Audit;
- Deep Audit;
- Operational Intelligence и Trends;
- Process Mining;
- Business Architecture Audit;
- Executive Intelligence Suite;
- Reference Model Audit;
- Automatic Capability Discovery;
- Evidence-Based Audit;
- Deep REST Evidence;
- Knowledge Base & Methodology;
- Executive Brief и Management Report;
- Reports & Export;
- Scheduling & Automation;
- System Health & Data Quality;
- Groq AI Coach;
- Developer Attribution & Brand Integrity.

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

ROI_HOURLY_COST_KZT=0
REFERENCE_MODEL_PROFILE=manufacturing_enterprise
```

## Развёртывание

```bash
cd /opt/ai-bit
git switch agent/import-current-ai-bit
git pull
docker compose build --no-cache browser-worker
docker compose up -d browser-worker
```

Проверка версии:

```bash
curl -sS http://127.0.0.1:8090/health | jq
```

Ожидаем:

```json
{
  "status": "ok",
  "version": "2.0.0-alpha.5",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Knowledge Base API

Получить весь каталог методик:

```bash
curl -sS http://127.0.0.1:8090/knowledge-base | jq
```

Получить методику конкретного направления:

```bash
curl -sS \
  http://127.0.0.1:8090/knowledge-base/contract_approval \
  | jq
```

Пересчитать эталонный аудит с методическими рекомендациями:

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/reference-audit/collect \
  | jq '{profile,coverage,summary,knowledge_base,critical_gaps}'
```

Проверить методику внутри конкретной возможности:

```bash
curl -sS \
  http://127.0.0.1:8090/reference-audit/latest \
  | jq '.capabilities[] | select(.id == "contract_approval") | {title,status,confidence,methodology,evidence_audit}'
```

## Deep REST Evidence API

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/deep-rest-evidence/collect \
  | jq '{configured,summary,probes,capabilities}'
```

## Ограничения alpha.5

- первая версия базы знаний покрывает основные управленческие контуры и будет расширяться;
- методика AI-BIT не является официальной сертификацией Bitrix24;
- рекомендации не заменяют владельца процесса и утверждённое техническое задание;
- REST-методы зависят от редакции Bitrix24 и прав webhook;
- статус `missing` допустим только при успешной проверке обязательных технических источников.

## Roadmap 2.0

- `2.0.0-alpha.1` — Reference Model Audit;
- `2.0.0-alpha.2` — Automatic Capability Discovery;
- `2.0.0-alpha.3` — Evidence-Based Audit;
- `2.0.0-alpha.4` — Deep REST Evidence и отказ от ручных статусов;
- `2.0.0-alpha.5` — Knowledge Base & Methodology;
- `2.0.0-alpha.6` — Evidence Matrix UI и редактор методики;
- `2.0.0-beta.1` — Target Roadmap;
- `2.0.0-beta.2` — AI Consultant;
- `2.0.0` — стабильная экспертная система цифровой трансформации.

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
