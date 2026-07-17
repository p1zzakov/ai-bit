# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Vision

Платформа обнаруживает проблемы, показывает фактические подтверждения, объясняет причины и формирует приоритетный план цифровой трансформации на основе данных портала.

## Principles

1. Только read-only работа с Bitrix24.
2. Каждый вывод должен иметь фактическое подтверждение.
3. Недостаток данных обозначается прямо, без домыслов.
4. AI работает только по переданным фактам.
5. Рекомендации содержат проблему, действие и приоритет.
6. Оценки должны быть воспроизводимыми и объяснимыми.
7. Авторство и контакт разработчика отображаются централизованно и проверяются через Brand Integrity.

## Текущая версия

Browser Worker: `1.0.0-rc.10`.

## Что добавлено в rc.10

### Отчёт для руководства без технических терминов

Groq собирает данные из всех аналитических контуров AI-BIT и формирует понятное управленческое заключение для генерального директора и руководителей подразделений.

Отчёт содержит:

- общую оценку внедрения Bitrix24;
- сильные стороны;
- основные слабые места;
- оценку администрирования и управления системой;
- организацию работы и контроль задач;
- бизнес-процессы;
- продажи и работу с клиентами;
- документооборот;
- автоматизацию;
- главные риски;
- приоритетные действия;
- план на 30 / 60 / 90 дней;
- итоговое заключение для руководства.

Текст формируется простым деловым русским языком без терминов `REST`, `webhook`, `crawl`, `JSON` и другого программного жаргона.

Поддерживаются два режима:

```text
Краткий отчёт   — ориентирован на 1–2 страницы
Подробный отчёт — развёрнутый анализ по всем направлениям
```

Доступны:

- просмотр в единой админке;
- копирование текста;
- HTML;
- PDF;
- JSON;
- история ранее сформированных отчётов.

## Unified Enterprise Admin

```text
http://SERVER_IP:8090/
http://SERVER_IP:8090/admin
```

Разделы:

```text
#executive
#implementation
#operations
#processes
#architecture
#reports
#management
#automation
#system
#about
```

Прямая ссылка на новый раздел:

```text
http://SERVER_IP:8090/management-report
```

## Основные модули

- Implementation Audit;
- Deep Audit;
- Operational Intelligence;
- Operational Trends 7/30/90;
- Process Mining;
- Business Process Audit;
- CRM Funnel Audit;
- Document Flow Audit;
- System Health & Data Quality;
- Groq AI Coach;
- Reports & Export;
- Management Report;
- Scheduling & Automation;
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
  "version": "1.0.0-rc.10",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Management Report API

Сформировать краткий отчёт:

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/management-reports/generate?mode=short' \
  | jq
```

Сформировать подробный отчёт:

```bash
curl -sS -X POST \
  'http://127.0.0.1:8090/management-reports/generate?mode=detailed' \
  | jq
```

Список отчётов:

```bash
curl -sS http://127.0.0.1:8090/management-reports | jq
```

Форматы скачивания:

```text
GET /management-reports/{REPORT_ID}/html
GET /management-reports/{REPORT_ID}/json
GET /management-reports/{REPORT_ID}/pdf
```

Артефакты сохраняются в:

```text
/app/artifacts/management-reports/
```

При стандартном volume mapping:

```text
/opt/ai-bit/reports/ui/management-reports/
```

## Интерфейсы

```text
http://SERVER_IP:8090/                       Unified Enterprise Admin
http://SERVER_IP:8090/executive              Executive Dashboard и AI Coach
http://SERVER_IP:8090/dashboard              Аудит внедрения
http://SERVER_IP:8090/operations             Operational Intelligence
http://SERVER_IP:8090/processes              Process Mining
http://SERVER_IP:8090/business-architecture  Business Architecture Audit
http://SERVER_IP:8090/reports-ui             Reports & Export
http://SERVER_IP:8090/management-report      Отчёт для руководства
http://SERVER_IP:8090/automation             Scheduling & Automation
http://SERVER_IP:8090/system                 System Health & Data Quality
http://SERVER_IP:8090/about                  О системе и разработчике
```

## Ограничения rc.10

- качество заключения зависит от свежести исходных данных;
- Groq не выдумывает отсутствующие сведения и должен обозначать недостаток данных;
- денежный эффект не рассчитывается без заданной стоимости рабочего часа;
- отчёт является поддержкой управленческого решения, а не заменой владельцев процессов;
- ранее сформированные отчёты автоматически не изменяются.

## Roadmap

- `alpha.1` — Unified Knowledge Graph и AI Provider Layer;
- `alpha.2` — динамика 7/30/90 дней;
- `beta.1` — Executive Dashboard и AI Coach;
- `beta.2` — Process Mining;
- `rc.1` — Business Process, CRM Funnel и Document Flow Audit;
- `rc.2` — Unified Enterprise Admin;
- `rc.3` — System Health & Data Quality;
- `rc.4` — Enterprise UI Refresh;
- `rc.5` — Reports & Export;
- `rc.6` — Scheduling & Automation;
- `rc.7` — Developer Attribution & Brand Integrity;
- `rc.8–rc.9` — Brand Cleanup и компактный info-icon;
- `rc.10` — Management Report без технического жаргона;
- `1.0.0` — стабилизация, тесты и релизная документация;
- `2.0` — Digital Maturity, AI Consultant, ROI, HeatMap и Digital Twin.

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
