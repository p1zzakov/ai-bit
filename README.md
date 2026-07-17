# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.3`.

## 2.0.0-alpha.3 — Evidence-Based Audit

AI-BIT больше не считает ручное утверждение достаточным доказательством наличия или отсутствия процесса. Каждый вывод строится по матрице:

```text
требование → проверенные источники → найденные факты → статус → уверенность
```

Статусы:

- `implemented` — найдены независимые подтверждения конфигурации и фактического использования;
- `partial` — найдены отдельные признаки, но полный маршрут или использование не подтверждены;
- `missing` — все обязательные источники доступны и проверены, подтверждений не найдено;
- `unknown` — данных недостаточно; не считается отсутствием.

Ручное подтверждение владельца процесса сохраняется как отдельный источник `manual_claim`, но не подменяет техническую проверку.

### Проверяемые источники

- карта и содержимое портала;
- Business Architecture Audit;
- Process Mining и фактические запуски;
- Operational Intelligence;
- Automatic Capability Discovery;
- подтверждение владельца процесса.

Для каждого процесса сохраняются:

- список обязательных источников;
- доступность каждого источника;
- найденные совпадения;
- источники фактического использования;
- итоговый статус;
- уверенность в процентах;
- понятное обоснование вывода.

На странице `#management` у разрывов эталонной модели появилась кнопка **«Показать доказательства»**.

## Главная ссылка для руководства

```text
http://SERVER_IP:8090/#management
```

Ссылка не меняется. Страница автоматически показывает Executive Brief, сравнение с эталонной моделью и доказательства по каждому существенному разрыву.

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

Проверка версии:

```bash
curl -sS http://127.0.0.1:8090/health | jq
```

Ожидаем:

```json
{
  "status": "ok",
  "version": "2.0.0-alpha.3",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## API доказательного аудита

Собрать доказательства:

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/evidence-audit/collect \
  | jq
```

Последний результат:

```bash
curl -sS \
  http://127.0.0.1:8090/evidence-audit/latest \
  | jq '{methodology,summary,capabilities}'
```

Пересчитать эталонный аудит с доказательной матрицей:

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/reference-audit/collect \
  | jq '{profile,coverage,summary,critical_gaps,evidence_audit}'
```

Проверить конкретный процесс:

```bash
curl -sS \
  http://127.0.0.1:8090/evidence-audit/latest \
  | jq '.capabilities.contract_approval'
```

Артефакты:

```text
/app/artifacts/capability-discovery/latest.json
/app/artifacts/evidence-audit/latest.json
/app/artifacts/reference-audit/latest.json
```

## Ограничения alpha.3

- методика AI-BIT не является официальной сертификацией Bitrix24;
- отрицательный вывод допустим только при доступности всех обязательных источников;
- текущий Automatic Capability Discovery использует агрегированные артефакты, поэтому часть процессов останется `unknown` до появления более детальных REST-проверок;
- ручные сведения учитываются, но не имеют исключительного приоритета;
- экономический эффект и Digital Maturity являются инструментами приоритизации.

## Roadmap 2.0

- `2.0.0-alpha.1` — Reference Model Audit;
- `2.0.0-alpha.2` — Automatic Capability Discovery;
- `2.0.0-alpha.3` — Evidence-Based Audit;
- `2.0.0-alpha.4` — детальные REST-проверки смарт-процессов, шаблонов, стадий и запусков;
- `2.0.0-beta.1` — отраслевые профили и редактор эталонной модели;
- `2.0.0-beta.2` — AI Consultant и целевая дорожная карта;
- `2.0.0` — стабильная экспертная система цифровой трансформации.

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
