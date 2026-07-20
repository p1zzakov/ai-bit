# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.15`.

## 2.0.0-alpha.15 — AI Process Optimizer

AI-BIT анализирует не только наличие процессов, но и качество их реализации. Источниками являются фактические артефакты Process Mining, Business Architecture и Deep REST Evidence.

Для каждого обнаруженного процесса рассчитываются:

- Process Score от 0 до 100;
- количество этапов и запусков;
- средняя длительность;
- наличие SLA;
- подтверждённые роботы и триггеры;
- ручные действия;
- циклы и обратные переходы;
- ошибки выполнения;
- зависимость от одного участника.

Статусы процессов:

- `optimized` — процесс в целом управляем;
- `improvable` — есть подтверждённые точки оптимизации;
- `redesign` — процесс требует переработки.

Каждая рекомендация сохраняется как структурированный объект:

```json
{
  "process": "Согласование договора",
  "category": "loops",
  "problem": "Обнаружены повторные согласования",
  "recommendation": "Исключить повторное прохождение подтверждённых этапов",
  "expected_effect": "Снижение повторной работы",
  "confidence": 93,
  "project_generator_payload": {}
}
```

`project_generator_payload` станет входом для будущего генератора проектов и задач Bitrix24.

На странице руководителя отображаются:

- общая оценка процессов;
- количество проверенных процессов;
- процессы, которые можно улучшить;
- процессы, требующие переработки;
- рейтинг процессов;
- десять приоритетных рекомендаций.

Если данных недостаточно, система показывает `insufficient_data` и не придумывает проблемы.

## 2.0.0-alpha.11–alpha.14 — Transformation Intelligence

На странице руководителя добавлен единый контур управления изменениями.

### alpha.11 — Roadmap Generator

Система преобразует подтверждённые корневые причины и разрывы эталонной модели в дорожную карту на 90 дней.

### alpha.12 — Executive Timeline

История строится только по сохранённым снимкам Executive Intelligence.

### alpha.13 — Evidence-Based Risk Forecast

Прогноз включается только при наличии минимум трёх исторических снимков. Если истории недостаточно, система показывает `insufficient_history`.

### alpha.14 — AI CIO

Блок **«Что бы сделал CIO в ближайшие 90 дней»** ранжирует приоритетные решения по подтверждённым отклонениям.

## Архитектура аудита

```text
Deep REST Evidence
→ Automatic Capability Discovery
→ Evidence-Based Audit
→ Knowledge Base & Methodology
→ Reference Model Audit
→ Process Mining
→ AI Process Optimizer
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
  "version": "2.0.0-alpha.15",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Проверка Process Optimizer

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  -o /tmp/executive-alpha15.json
```

```bash
jq '{
  status: .process_optimizer.status,
  overall_score: .process_optimizer.overall_score,
  summary: .process_optimizer.summary,
  processes: .process_optimizer.processes,
  top_recommendations: .process_optimizer.top_recommendations
}' /tmp/executive-alpha15.json
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
