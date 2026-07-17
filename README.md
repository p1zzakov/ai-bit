# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.14`.

## 2.0.0-alpha.11–alpha.14 — Transformation Intelligence

На странице руководителя добавлен единый контур управления изменениями.

### alpha.11 — Roadmap Generator

Система преобразует подтверждённые корневые причины и разрывы эталонной модели в дорожную карту на 90 дней:

- стабилизация управления — 1–2 недели;
- завершение ключевых процессов — 3–6 недель;
- масштабирование и оптимизация — 7–12 недель.

Для каждого пункта указываются причина, действие, роль ответственного, критерий завершения и уверенность вывода.

### alpha.12 — Executive Timeline

История строится только по сохранённым снимкам Executive Intelligence. Отображаются:

- цифровая зрелость;
- покрытие эталонной модели;
- просрочка;
- количество задач без срока;
- изменение показателей относительно первого доступного снимка.

### alpha.13 — Evidence-Based Risk Forecast

Прогноз включается только при наличии минимум трёх исторических снимков. Используется линейная экстраполяция фактической динамики. Если истории недостаточно, система показывает `insufficient_history` и не придумывает прогноз.

### alpha.14 — AI CIO

Блок **«Что бы сделал CIO в ближайшие 90 дней»** ранжирует до семи приоритетных решений и показывает:

```text
проблема
→ почему это важно
→ какое решение принять
→ кто должен отвечать
→ срок
→ уверенность вывода
```

Groq не принимает управленческие решения. Рекомендации формируются детерминированно по доказанным отклонениям AI-BIT.

Результат сохраняется в Executive Intelligence:

```json
{
  "transformation_roadmap": {},
  "executive_timeline": {},
  "risk_forecast": {},
  "ai_cio": {}
}
```

Главная ссылка остаётся прежней:

```text
http://SERVER_IP:8090/#management
```

## 2.0.0-alpha.10 — Executive KPI Center + Root Cause Analysis

На странице руководителя рассчитываются KPI внедрения, использования, управления, исполнения, автоматизации, CRM и документооборота. Для каждого существенного отклонения формируется цепочка:

```text
Факт
→ корневая причина
→ влияние на бизнес
→ рекомендуемое действие
→ уверенность вывода
```

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

Денежные показатели используют ставку:

```env
ROI_HOURLY_COST_KZT=4000
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
→ Executive KPI Center
→ Root Cause Analysis
→ Roadmap Generator
→ Executive Timeline
→ Evidence-Based Risk Forecast
→ AI CIO
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
  "version": "2.0.0-alpha.14",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Проверка Transformation Intelligence

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  -o /tmp/executive-alpha14.json
```

```bash
jq '{
  roadmap: .transformation_roadmap,
  timeline: .executive_timeline,
  forecast: .risk_forecast,
  ai_cio: .ai_cio
}' /tmp/executive-alpha14.json
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
