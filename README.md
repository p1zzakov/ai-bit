# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.9`.

## 2.0.0-alpha.9 — Advanced Business Value Engine

Страница руководителя рассчитывает расширенный бизнес-эффект внедрения:

- автоматизация повторяющихся операций;
- бумага, печать и архивирование;
- потери рабочего времени из-за просроченных задач;
- дополнительный контроль задач без срока;
- время руководителей на ручной сбор статусов;
- время сотрудников на поиск документов;
- ожидаемое ускорение согласований;
- индикативная стоимость неиспользуемого потенциала Bitrix24;
- совокупный консервативный эффект в часах и тенге.

Главная ссылка остаётся прежней:

```text
http://SERVER_IP:8090/#management
```

### Принципы расчёта

Денежные показатели используют ставку:

```env
ROI_HOURLY_COST_KZT=4000
```

Базовые усреднённые параметры:

```env
PAPER_PAGES_PER_USER_MONTH=25
PAPER_BLENDED_PAGE_COST_KZT=15
PAPER_REDUCTION_RATE=0.60
VALUE_OVERDUE_MINUTES_PER_TASK_MONTH=30
VALUE_NO_DEADLINE_MINUTES_PER_TASK_MONTH=15
VALUE_DOCUMENT_SEARCH_HOURS_USER_MONTH=0.5
VALUE_MANAGEMENT_HOURS_DEPARTMENT_MONTH=1.5
VALUE_APPROVAL_REDUCTION_RATE=0.50
```

Неиспользуемый потенциал и ускорение согласований показываются отдельно и не прибавляются повторно к совокупному итогу.

### Структура результата

```json
{
  "business_value": {
    "labor": {},
    "paper": {},
    "overdue_losses": {},
    "no_deadline_losses": {},
    "management_time": {},
    "document_search": {},
    "approvals": {},
    "unused_potential": {},
    "total": {}
  }
}
```

## Архитектура аудита

```text
Deep REST Evidence
→ Automatic Capability Discovery
→ Evidence-Based Audit
→ Knowledge Base & Methodology
→ Reference Model Audit
→ Executive Intelligence
→ Management Conclusion
→ Advanced Business Value Engine
→ Resilient Executive Brief
```

Статусы возможностей:

- `implemented` — подтверждены конфигурация и использование;
- `partial` — найдены отдельные признаки, но полный маршрут не подтверждён;
- `missing` — все обязательные источники проверены, подтверждений нет;
- `unknown` — данных недостаточно, отсутствием не считается.

Ручные пожелания не устанавливают статус и не влияют на итоговую оценку.

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

Проверка:

```bash
curl -sS http://127.0.0.1:8090/health | jq
```

Ожидаем:

```json
{
  "status": "ok",
  "version": "2.0.0-alpha.9",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Проверка бизнес-эффекта

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  | jq '.business_value'
```

Краткая сводка:

```bash
curl -sS \
  http://127.0.0.1:8090/executive-intelligence/latest \
  | jq '{
      labor: .business_value.labor,
      paper: .business_value.paper,
      overdue: .business_value.overdue_losses,
      no_deadline: .business_value.no_deadline_losses,
      management: .business_value.management_time,
      document_search: .business_value.document_search,
      approvals: .business_value.approvals,
      unused_potential: .business_value.unused_potential,
      total: .business_value.total
    }'
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
