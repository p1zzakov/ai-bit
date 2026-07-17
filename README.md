# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.6`.

## 2.0.0-alpha.6 — Resilient Executive Brief

Страница руководителя больше не зависит от Groq и не блокируется при недоступности внешнего AI-провайдера.

Главная ссылка остаётся прежней:

```text
http://SERVER_IP:8090/#management
```

Новая схема загрузки:

```text
открытие страницы
→ мгновенный показ последнего подтверждённого Executive Intelligence snapshot
→ фоновое обновление данных
→ автоматическая замена сводки после успешного расчёта
```

Groq используется только для дополнительного текстового оформления подробного отчёта. Ошибка Groq не влияет на Executive Brief.

### Что показывает Executive Brief

- Digital Maturity;
- просрочку и задачи без срока;
- сотрудников и подразделения в зоне риска;
- сравнение с эталонной моделью;
- доказательства по каждому существенному разрыву;
- рекомендации из Knowledge Base;
- ROI в часах и тенге;
- решения, требующие утверждения руководства;
- последний подтверждённый снимок при ошибке обновления.

### Отказоустойчивость

- `GET /executive-intelligence/latest` используется для мгновенной загрузки;
- `POST /executive-intelligence/collect` выполняется в фоне;
- запросы имеют ограничение времени ожидания;
- при ошибке обновления сохраняется последний подтверждённый результат;
- экран больше не остаётся на сообщении «Формируется управленческая сводка»;
- автоматическое фоновое обновление выполняется раз в 15 минут.

## Архитектура аудита

```text
Deep REST Evidence
→ Automatic Capability Discovery
→ Evidence-Based Audit
→ Knowledge Base & Methodology
→ Reference Model Audit
→ Executive Intelligence
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

ROI_HOURLY_COST_KZT=0
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
  "version": "2.0.0-alpha.6",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Проверка Executive Brief

```bash
time curl -sS http://127.0.0.1:8090/executive-intelligence/latest | jq '{generated_at,digital_maturity,source_summary,reference_audit,roi}'
```

Принудительное обновление:

```bash
curl -sS -X POST http://127.0.0.1:8090/executive-intelligence/collect | jq '{generated_at,digital_maturity,source_summary}'
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
