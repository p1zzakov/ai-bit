# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа доказательного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

**AI-BIT Enterprise `2.2.0` — Executive UX & Bitrix Digital Passport**

Главный принцип продукта:

> неизвестное не считается отсутствующим, а управленческие выводы формируются только по подтверждённым данным.

## Что изменилось в 2.2.0

### Разгруженный отчёт для руководства

Страница `#management` переведена на трёхуровневую модель:

1. **30 секунд** — общая оценка, критичные проблемы, просрочка, задачи без срока и потенциальный экономический эффект;
2. **управленческий вывод** — краткое объяснение ситуации и одно следующее действие;
3. **детализация по запросу** — ссылки на специализированные аналитические страницы и раскрываемые доказательства.

Тяжёлые блоки больше не выводятся подряд на главной странице руководителя.

### Bitrix Digital Passport

Отдельный экран цифрового паспорта показывает на одном экране:

- общий индекс внедрения;
- CRM;
- документооборот;
- автоматизацию;
- бизнес-процессы;
- исполнительскую дисциплину;
- управленческую дисциплину;
- покрытие эталонной модели;
- использование системы;
- просрочку и задачи без срока.

Показатель без подтверждённых данных отображается как `нет данных`, а не заменяется выдуманной оценкой.

### Специализированные страницы

- `/digital-passport` — цифровой паспорт Bitrix24;
- `/process-optimizer` — рейтинг процессов, узкие места и рекомендации;
- `/ai-cio` — приоритетные управленческие решения на 90 дней;
- `/transformation-roadmap` — этапы, сроки и ответственные роли;
- `/risk-forecast` — прогноз по накопленной исторической динамике;
- `/business-value` — экономика внедрения и состав ожидаемого эффекта.

## Функциональные контуры

### Executive Intelligence

- управленческое заключение без технических терминов;
- Executive KPI Center;
- Root Cause Analysis;
- AI CIO;
- краткая сводка без обязательной зависимости от Groq.

### Process Intelligence

- Process Mining;
- AI Process Optimizer;
- Process Score от 0 до 100;
- кандидаты на автоматизацию;
- анализ маршрутов постановщик → исполнитель;
- поиск узких мест и зависимости от отдельных сотрудников;
- структурированные рекомендации под будущий Project Generator.

### Transformation Intelligence

- дорожная карта на 90 дней;
- Executive Timeline;
- доказательный прогноз рисков при наличии достаточной истории;
- приоритизация действий по влиянию, срочности и уверенности вывода.

### Business Value

- экономия рабочего времени;
- финансовый эффект по ставке `ROI_HOURLY_COST_KZT`;
- бумага, печать и архивирование;
- потери из-за просрочки и задач без срока;
- время руководителей на ручной контроль;
- поиск документов;
- ускорение согласований;
- индикативная стоимость неиспользуемого потенциала Bitrix24.

### Evidence Platform

- Deep REST Evidence;
- Automatic Capability Discovery;
- Evidence-Based Audit;
- Knowledge Base & Methodology;
- Reference Model Audit;
- статусы `implemented`, `partial`, `missing`, `unknown`;
- ручные пожелания не влияют на итоговую оценку.

## Архитектура

```text
Bitrix24 Browser + REST
        ↓
Deep REST Evidence
        ↓
Capability Discovery
        ↓
Evidence Engine + Knowledge Base
        ↓
Reference Model Audit
        ↓
Process Mining + Process Optimizer
        ↓
Executive Intelligence
        ↓
Management Conclusion + KPI + Root Cause
        ↓
Business Value + Roadmap + Timeline + Risk Forecast + AI CIO
        ↓
Compact #management + Specialized Portals + Digital Passport
```

## Основные интерфейсы

```text
http://SERVER_IP:8090/                       Unified Enterprise Admin
http://SERVER_IP:8090/#management            Краткий отчёт для руководства
http://SERVER_IP:8090/digital-passport       Цифровой паспорт Bitrix24
http://SERVER_IP:8090/process-optimizer      AI Process Optimizer
http://SERVER_IP:8090/ai-cio                 AI CIO
http://SERVER_IP:8090/transformation-roadmap Дорожная карта
http://SERVER_IP:8090/risk-forecast          Прогноз рисков
http://SERVER_IP:8090/business-value         Бизнес-эффект
http://SERVER_IP:8090/executive-intelligence Executive Intelligence Suite
http://SERVER_IP:8090/dashboard              Аудит внедрения
http://SERVER_IP:8090/operations             Operational Intelligence
http://SERVER_IP:8090/processes              Process Mining
http://SERVER_IP:8090/business-architecture  Business Architecture Audit
http://SERVER_IP:8090/reports-ui             Reports & Export
http://SERVER_IP:8090/automation             Scheduling & Automation
http://SERVER_IP:8090/system                 System Health & Data Quality
http://SERVER_IP:8090/about                  HTML-страница о системе
http://SERVER_IP:8090/about/meta             JSON-метаданные
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

ROI_HOURLY_COST_KZT=4000
REFERENCE_MODEL_PROFILE=manufacturing_enterprise
```

## Обновление

```bash
cd /opt/ai-bit

git switch agent/import-current-ai-bit
git pull

docker compose build --no-cache browser-worker
docker compose up -d browser-worker
```

## Проверка версии

```bash
curl -sS http://127.0.0.1:8090/health | jq
curl -sS http://127.0.0.1:8090/about/meta | jq
```

Ожидаем версию:

```json
{
  "version": "2.2.0"
}
```

Проверка новых маршрутов:

```bash
curl -sS http://127.0.0.1:8090/openapi.json \
  | jq '.paths | keys | map(select(test("digital-passport|process-optimizer|ai-cio|transformation-roadmap|risk-forecast|business-value")))'
```

## Полный пересчёт

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  -o /tmp/executive-2.2.0.json
```

```bash
jq '{
  version,
  conclusion: .management_conclusion,
  kpi: .executive_kpi.summary,
  process_optimizer: .process_optimizer.summary,
  roadmap: .transformation_roadmap,
  forecast: .risk_forecast.status,
  ai_cio: .ai_cio.recommendations,
  business_value: .business_value.total
}' /tmp/executive-2.2.0.json
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
© 2026. Все права защищены.
```
