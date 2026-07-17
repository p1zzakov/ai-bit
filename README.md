# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.4`.

## 2.0.0-alpha.4 — Deep REST Evidence

AI-BIT формирует статусы процессов только по данным, которые система получила и проверила самостоятельно.

Ручные пожелания и утверждения владельца проекта:

- не устанавливают статус `missing`;
- не снижают Digital Maturity;
- не создают риски и рекомендации;
- не выводятся в отчёте руководителя как установленный факт.

Эталонная модель определяет, какие возможности рекомендуется проверить, но результат определяется доказательной матрицей.

### Прямые REST-проверки

Система выполняет read-only запросы к Bitrix24 и проверяет доступные сущности:

- типы смарт-процессов;
- CRM-категории и стадии;
- сделки и признаки фактической активности;
- шаблоны и экземпляры бизнес-процессов;
- универсальные списки;
- CRM-формы;
- хранилища Диска.

Недоступный или неподдерживаемый REST-метод не считается доказательством отсутствия процесса.

### Правила статусов

- `implemented` — REST и независимые источники подтверждают конфигурацию и использование;
- `partial` — найдены отдельные системные признаки, но полный маршрут или использование не подтверждены;
- `missing` — все обязательные технические источники доступны и проверены, подтверждений нет;
- `unknown` — данных недостаточно; не считается отсутствием.

Каждый вывод содержит:

- проверенные источники;
- доступность источников;
- найденные факты;
- итоговый статус;
- уверенность;
- понятное обоснование.

## Главная ссылка для руководства

```text
http://SERVER_IP:8090/#management
```

Ссылка не меняется. На странице отображаются только выводы, подтверждённые самой системой. Для каждого существенного разрыва доступен блок **«Показать доказательства»**.

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
  "version": "2.0.0-alpha.4",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Deep REST Evidence API

Запустить прямые REST-проверки:

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/deep-rest-evidence/collect \
  | jq
```

Посмотреть доступность методов:

```bash
curl -sS \
  http://127.0.0.1:8090/deep-rest-evidence/latest \
  | jq '{configured,summary,probes}'
```

## Доказательный аудит

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/evidence-audit/collect \
  | jq '{methodology,deep_rest_summary,summary,capabilities}'
```

Проверить согласование договоров:

```bash
curl -sS \
  http://127.0.0.1:8090/evidence-audit/latest \
  | jq '.capabilities.contract_approval'
```

Пересчитать эталонный аудит:

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/reference-audit/collect \
  | jq '{profile,coverage,summary,critical_gaps,evidence_audit}'
```

Артефакты:

```text
/app/artifacts/deep-rest-evidence/latest.json
/app/artifacts/capability-discovery/latest.json
/app/artifacts/evidence-audit/latest.json
/app/artifacts/reference-audit/latest.json
```

## Ограничения alpha.4

- REST-методы зависят от редакции Bitrix24 и прав входящего webhook;
- ошибка или отсутствие права на метод переводит источник в недоступный, а не в отрицательный;
- `missing` допустим только при успешной проверке всех обязательных технических источников;
- методика AI-BIT не является официальной сертификацией Bitrix24;
- экономический эффект и Digital Maturity являются инструментами приоритизации.

## Roadmap 2.0

- `2.0.0-alpha.1` — Reference Model Audit;
- `2.0.0-alpha.2` — Automatic Capability Discovery;
- `2.0.0-alpha.3` — Evidence-Based Audit;
- `2.0.0-alpha.4` — Deep REST Evidence и отказ от ручных статусов;
- `2.0.0-alpha.5` — Evidence Matrix UI;
- `2.0.0-beta.1` — Target Roadmap;
- `2.0.0-beta.2` — AI Consultant;
- `2.0.0` — стабильная экспертная система цифровой трансформации.

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
