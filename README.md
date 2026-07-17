# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.8`.

## 2.0.0-alpha.8 — Business Value Calculator

На странице руководителя появился прозрачный расчёт бизнес-эффекта:

- экономия рабочего времени;
- денежный эквивалент рабочего времени;
- средняя стоимость часа, использованная в расчёте;
- ориентировочная экономия на бумаге и печати после внедрения электронного документооборота;
- совокупный прогнозируемый эффект.

Главная ссылка остаётся прежней:

```text
http://SERVER_IP:8090/#management
```

### Экономия рабочего времени

Финансовый эффект рассчитывается по фактическим кандидатам на автоматизацию и ставке:

```env
ROI_HOURLY_COST_KZT=4000
```

На странице явно указывается:

```text
До 269 рабочих часов в год
Экономия рабочего времени — ориентировочно 1 076 000 ₸ в год
Расчёт выполнен по средней стоимости рабочего часа 4 000 ₸
```

### Экономия на бумажном документообороте

Для первичной оценки используется усреднённая методика AI-BIT:

- 25 печатных страниц на одного активного пользователя в месяц;
- 15 ₸ совокупной стоимости одной страницы;
- сокращение печати на 60% после внедрения электронного документооборота.

В стоимость страницы включены:

- бумага;
- тонер и картриджи;
- ресурс печатающей техники;
- сопутствующие расходы на печать.

Расчёт выполняется по количеству активных пользователей, полученному из Bitrix24. Результат помечается как ориентировочный и не подменяет финансово-экономическое обоснование.

При необходимости средний сценарий можно изменить:

```env
PAPER_PAGES_PER_USER_MONTH=25
PAPER_BLENDED_PAGE_COST_KZT=15
PAPER_REDUCTION_RATE=0.60
```

### Совокупный эффект

```text
экономия рабочего времени
+
экономия на бумаге и печати
=
совокупный прогнозируемый эффект в год
```

Результат сохраняется в:

```json
{
  "business_value": {
    "labor": {},
    "paper": {},
    "total": {}
  }
}
```

## 2.0.0-alpha.7 — Management Conclusion

На странице руководителя присутствует обязательный текстовый блок **«Заключение AI-BIT»**. Он формируется встроенным Decision Engine и не зависит от Groq.

Заключение отвечает на пять управленческих вопросов:

- что происходит;
- почему это происходит;
- чем это грозит компании;
- что необходимо утвердить руководству;
- какой эффект ожидается после исправления.

AI-BIT также ищет наиболее раннюю подтверждённую дату рабочей активности и показывает наблюдаемый срок внедрения.

## 2.0.0-alpha.6 — Resilient Executive Brief

Страница руководителя не зависит от Groq и не блокируется при недоступности внешнего AI-провайдера.

```text
открытие страницы
→ мгновенный показ последнего подтверждённого Executive Intelligence snapshot
→ фоновое обновление данных
→ автоматическая замена сводки после успешного расчёта
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
→ Business Value Calculator
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

PAPER_PAGES_PER_USER_MONTH=25
PAPER_BLENDED_PAGE_COST_KZT=15
PAPER_REDUCTION_RATE=0.60
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
  "version": "2.0.0-alpha.8",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Проверка бизнес-эффекта

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  | jq '{management_conclusion,business_value}'
```

Только расчёт бумаги и печати:

```bash
curl -sS \
  http://127.0.0.1:8090/executive-intelligence/latest \
  | jq '.business_value.paper'
```

Проверка ставки рабочего часа:

```bash
curl -sS \
  http://127.0.0.1:8090/executive-intelligence/latest \
  | jq '.business_value.labor'
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
