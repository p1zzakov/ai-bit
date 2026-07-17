# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Vision

Платформа не только анализирует текущее состояние портала, но и сравнивает фактическое внедрение с эталонной моделью цифрового управления компанией.

## Principles

1. Только read-only работа с Bitrix24.
2. Каждый вывод должен иметь фактическое подтверждение.
3. Недостаток данных обозначается прямо, без домыслов.
4. AI работает только по переданным фактам.
5. Рекомендации содержат проблему, действие и приоритет.
6. Оценки должны быть воспроизводимыми и объяснимыми.
7. Авторство и контакт разработчика отображаются централизованно.
8. Отсутствующие возможности определяются через сравнение с эталонной моделью, а не только через анализ уже существующих модулей.

## Текущая версия

Browser Worker: `2.0.0-alpha.1`.

## Что добавлено в 2.0.0-alpha.1

### Reference Model Audit

AI-BIT получил эталонную модель идеального внедрения для производственного предприятия. Теперь система отвечает на два разных вопроса:

```text
Что в Bitrix24 настроено неправильно?
Чего в Bitrix24 вообще не хватает?
```

Reference Model Audit:

- инвентаризирует доступные результаты аудитов;
- сравнивает их с перечнем рекомендуемых корпоративных возможностей;
- разделяет статусы `implemented`, `partial`, `missing`, `unknown`;
- рассчитывает процент покрытия эталонной модели;
- строит оценку по направлениям;
- выделяет критические отсутствующие процессы;
- снижает Digital Maturity при существенных пробелах;
- передаёт разрывы в Executive Intelligence и на страницу `#management`.

Первый профиль:

```text
Производственное предприятие
```

В эталон включены задачи, CRM, бизнес-процессы, документооборот, согласование договоров, служебные записки, заявки ИТ, создание пользователей, HR-процессы, закупки, оплаты, ремонты, база знаний и управленческий контроль.

Подтверждённые отсутствующие процессы:

- электронный обмен документами;
- согласование договоров;
- заявка на создание пользователя в AD и 1С;
- служебные записки.

Они имеют статус `missing` и отображаются как фактические разрывы целевой модели.

## Главная ссылка для руководства

```text
http://SERVER_IP:8090/#management
```

Ссылка не меняется. На странице автоматически отображаются:

- состояние компании;
- Digital Maturity;
- покрытие эталонной модели;
- количество реализованных, отсутствующих и непроверенных возможностей;
- критические разрывы;
- ключевые процессы, которые не внедрены;
- риски, решения руководства, подразделения и ROI.

## Основные модули

- Implementation Audit;
- Deep Audit;
- Operational Intelligence;
- Operational Trends 7/30/90;
- Process Mining;
- Business Architecture Audit;
- Executive Intelligence Suite;
- Reference Model Audit;
- Executive Brief;
- Management Report;
- Reports & Export;
- Scheduling & Automation;
- System Health & Data Quality;
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

SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Almaty
SCHEDULER_POLL_SECONDS=30
SCHEDULER_OPERATIONS_ENABLED=true
SCHEDULER_OPERATIONS_SCHEDULE=daily@06:00
SCHEDULER_BUSINESS_ARCHITECTURE_ENABLED=true
SCHEDULER_BUSINESS_ARCHITECTURE_SCHEDULE=weekly:mon@07:00
SCHEDULER_CRAWL_ENABLED=true
SCHEDULER_CRAWL_SCHEDULE=weekly:sun@03:00
SCHEDULER_EXECUTIVE_REPORT_ENABLED=true
SCHEDULER_EXECUTIVE_REPORT_SCHEDULE=monthly:1@08:00
```

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
  "status": "ok",
  "version": "2.0.0-alpha.1",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Reference Model API

Получить активную эталонную модель:

```bash
curl -sS http://127.0.0.1:8090/reference-model | jq
```

Запустить сравнение:

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/reference-audit/collect \
  | jq
```

Краткая сводка:

```bash
curl -sS \
  http://127.0.0.1:8090/reference-audit/latest \
  | jq '{profile,coverage,summary,domains,critical_gaps,requires_verification}'
```

Артефакт:

```text
/app/artifacts/reference-audit/latest.json
```

## Executive Intelligence API

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  | jq '{digital_maturity,reference_audit,risks,missing_capabilities,roi}'
```

## Management Report API

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/management-reports/generate?mode=detailed' \
  | jq
```

## Интерфейсы

```text
http://SERVER_IP:8090/                       Unified Enterprise Admin
http://SERVER_IP:8090/#management            Сводка руководителя и эталонное сравнение
http://SERVER_IP:8090/executive-intelligence Executive Intelligence Suite
http://SERVER_IP:8090/dashboard              Аудит внедрения
http://SERVER_IP:8090/operations             Operational Intelligence
http://SERVER_IP:8090/processes              Process Mining
http://SERVER_IP:8090/business-architecture  Business Architecture Audit
http://SERVER_IP:8090/reports-ui             Reports & Export
http://SERVER_IP:8090/automation             Scheduling & Automation
http://SERVER_IP:8090/system                 System Health & Data Quality
http://SERVER_IP:8090/about                  О системе и разработчике
```

## Ограничения alpha.1

- автоматическое доказательство внедрения пока работает только для возможностей, по которым есть надёжные источники данных;
- статус `unknown` означает «требует проверки», а не «не реализовано»;
- ручные подтверждённые требования компании имеют приоритет над эвристикой;
- эталонная модель является методикой AI-BIT и должна расширяться отраслевыми профилями;
- Digital Maturity и ROI являются инструментами приоритизации, а не сертификационным заключением.

## Roadmap 2.0

- `2.0.0-alpha.1` — Reference Model Audit и профиль производственного предприятия;
- `2.0.0-alpha.2` — автоматическое обнаружение смарт-процессов, шаблонов и маршрутов;
- `2.0.0-alpha.3` — отраслевые профили и редактор эталонной модели;
- `2.0.0-beta.1` — доказательная матрица «требование → факт → статус»;
- `2.0.0-beta.2` — AI Consultant и целевая дорожная карта внедрения;
- `2.0.0` — стабильная экспертная система цифровой трансформации.

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
