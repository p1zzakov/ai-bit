# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа доказательного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

**AI-BIT Enterprise `2.1.0` — Intelligent Transformation Suite**

Главный принцип продукта:

> неизвестное не считается отсутствующим, а управленческие выводы формируются только по подтверждённым данным.

## Что входит в 2.1.0

### Executive Intelligence

- управленческое заключение без технических терминов;
- Executive KPI Center;
- Root Cause Analysis;
- AI CIO — приоритетные решения на 90 дней;
- детерминированный Executive Summary без обязательной зависимости от Groq.

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

### Platform

- Unified Enterprise Admin;
- Reports & Export;
- Scheduling & Automation;
- System Health & Data Quality;
- исторические снимки;
- безопасный fallback при недоступности Groq.

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
#management
```

## Основные интерфейсы

```text
http://SERVER_IP:8090/                       Unified Enterprise Admin
http://SERVER_IP:8090/#management            Сводка руководителя
http://SERVER_IP:8090/executive-intelligence Executive Intelligence Suite
http://SERVER_IP:8090/dashboard              Аудит внедрения
http://SERVER_IP:8090/operations             Operational Intelligence
http://SERVER_IP:8090/processes              Process Mining
http://SERVER_IP:8090/business-architecture  Business Architecture Audit
http://SERVER_IP:8090/reports-ui             Reports & Export
http://SERVER_IP:8090/automation             Scheduling & Automation
http://SERVER_IP:8090/system                 System Health & Data Quality
http://SERVER_IP:8090/about                  Информация о релизе
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
```

Ожидаем:

```json
{
  "status": "ok",
  "version": "2.1.0",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

Информация о релизе:

```bash
curl -sS http://127.0.0.1:8090/about | jq
```

## Полный пересчёт

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  -o /tmp/executive-2.1.0.json
```

Краткая проверка:

```bash
jq '{
  version,
  conclusion: .management_conclusion,
  kpi: .executive_kpi.summary,
  process_optimizer: .process_optimizer.summary,
  roadmap: .transformation_roadmap,
  timeline: .executive_timeline.status,
  forecast: .risk_forecast.status,
  ai_cio: .ai_cio.recommendations,
  business_value: .business_value.total
}' /tmp/executive-2.1.0.json
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
© 2026. Все права защищены.
```
