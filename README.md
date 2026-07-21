# AI-BIT Enterprise 5.0

> **Read-only платформа доказательного аудита, контроля качества и проектирования корпоративных интеграций Bitrix24 ↔ 1С.**

AI-BIT Enterprise превращает разрозненные технические данные Bitrix24 и 1С в проверяемое экспертное заключение: что реализовано корректно, где есть архитектурный риск, какие данные могут теряться или дублироваться, что обязан исправить интегратор и по каким критериям принимать работу.

Система не изменяет Bitrix24 и 1С. Она собирает evidence, строит карту интеграции, оценивает реализацию по лучшим практикам и формирует рекомендации в режиме `proposal only`.

---

## Текущая версия

**AI-BIT Enterprise `5.0.0` — Unified Integration Intelligence Platform**

Главные принципы:

- неизвестное не считается отсутствующим;
- отсутствие evidence не считается доказанным дефектом;
- критические выводы формируются только по подтверждённым фактам;
- каждый вывод должен быть воспроизводимым и трассируемым;
- автоматическая запись в Bitrix24 и 1С запрещена;
- рекомендации являются предложениями, а не скрытыми изменениями;
- бизнес-заключение и технический акт формируются раздельно.

---

## Зачем нужен AI-BIT

Типичная интеграция Bitrix24 ↔ 1С со временем превращается в набор обработок, пользовательских полей, webhook-ов, регламентных заданий и неформальных договорённостей. Часто никто не может точно ответить:

- какая система является источником истины;
- какой идентификатор связывает объекты;
- почему повторная выгрузка не создаёт дубль;
- что происходит при ошибке или недоступности одной из систем;
- какие поля действительно синхронизируются;
- сколько объектов потеряно или расходится;
- где находится журнал обмена;
- можно ли безопасно принять интеграцию в промышленную эксплуатацию.

AI-BIT создаёт единый доказательный контур и отвечает на эти вопросы на основе фактических данных.

---

## Что умеет версия 5.0

### 1. Evidence Engine 2.0

Каждое подтверждённое замечание получает собственный evidence bundle:

- код проверки;
- источник факта;
- обнаруженное значение;
- уровень уверенности;
- криптографический fingerprint evidence;
- решение `confirmed` или `requires_additional_evidence`;
- правило оспаривания вывода новым проверяемым evidence.

AI-BIT не просто утверждает, что интеграция реализована неправильно. Он показывает, на основании чего сделан вывод и как его воспроизвести.

### 2. Data Quality Engine

Контур предназначен для безопасной сверки фактических данных двух систем:

- количество объектов;
- записи только в Bitrix24;
- записи только в 1С;
- дубликаты внешних идентификаторов;
- расхождения ключевых значений;
- доля успешно сопоставленных записей;
- дата последней синхронизации;
- задержка обмена;
- ошибки и повторные попытки;
- контрольная выборка объектов.

До настройки read-only выборок система честно показывает `configuration_required`, а не придумывает оценку качества данных.

### 3. Drift Detection Engine

Каждый аудит формирует fingerprint архитектуры интеграции:

- карта сущностей;
- карта полей;
- активные точки обмена;
- архитектурные контроли;
- подтверждённые findings.

Последующие проверки смогут обнаруживать drift:

- изменение объекта 1С;
- изменение маппинга поля;
- исчезновение внешнего ключа;
- появление новой обработки обмена;
- изменение механизма очереди или повторных попыток;
- изменение промышленного допуска.

Изменение само по себе не считается ошибкой — сначала оценивается его влияние.

### 4. Business Impact Engine

Техническое замечание переводится в понятный бизнес-риск:

- вероятность проявления;
- критичность;
- затронутый процесс;
- возможная потеря данных;
- риск дублей;
- искажение аналитики;
- влияние на работу менеджеров, бухгалтерии и склада;
- приоритет исправления.

### 5. AI Integrator Copilot

Copilot формирует проектные playbook-ы для интегратора и 1С-разработчика:

- рекомендуемая архитектура;
- мастер-система;
- стратегия GUID;
- идемпотентность;
- схема retry/queue;
- журналирование;
- контроль конфликтов;
- требования к мониторингу;
- критерии приёмки;
- вопросы, на которые интегратор обязан ответить;
- анти-паттерны, которые нельзя использовать.

Режим Copilot — `read_only_advisory`.

---

## Два уровня заключения

### Для руководства

Отчёт без технической перегрузки:

- общая оценка качества;
- понятный вердикт;
- допуск к промышленной эксплуатации;
- что работает правильно;
- что реализовано неправильно;
- чем это грозит бизнесу;
- что необходимо переделать;
- план исправления по приоритетам;
- понятный критерий завершения каждого этапа.

### Для интегратора и 1С-программиста

Технический акт содержит:

- контрольный код `INT-XXX`;
- severity;
- фактическую реализацию;
- evidence Bitrix24 и 1С;
- нарушенный архитектурный принцип;
- сценарий отказа;
- требуемую реализацию;
- точный acceptance test;
- матрицу полей;
- неподтверждённые контроли;
- блокирующие условия промышленного допуска.

---

## Архитектура платформы

```text
Bitrix24 Browser / REST / Deep REST Evidence
                    │
                    ▼
          Capability Discovery
                    │
                    ▼
1C HTTP Service ── MCP-1C ── Metadata / Structures / Logs
                    │
                    ▼
        Unified Evidence & Knowledge Core
                    │
        ┌───────────┼────────────┬──────────────┐
        ▼           ▼            ▼              ▼
 Evidence 2.0   Data Quality   Drift Engine   Business Impact
        │           │            │              │
        └───────────┴────────────┴──────────────┘
                    │
                    ▼
        Best-Practice Assessment Engine
                    │
                    ▼
        Recommendation & Copilot Engine
                    │
           ┌────────┴────────┐
           ▼                 ▼
  Management Conclusion   Technical Act
```

---

## Проверяемые области интеграции

- компании ↔ контрагенты;
- контакты ↔ контактные лица;
- сделки ↔ заказы клиентов;
- товары ↔ номенклатура;
- счета ↔ документы оплаты;
- внешние идентификаторы;
- статусы и переходы;
- даты и суммы;
- единицы измерения и цены;
- мастер-система;
- идемпотентность;
- очередь и retry;
- инкрементальный обмен;
- обработка конфликтов;
- логирование и мониторинг;
- контроль фактических данных.

---

## Политика безопасности

AI-BIT Enterprise 5.0 работает по принципу минимального воздействия:

```text
Bitrix24 write: false
1C write: false
Automatic remediation: false
Proposal only: true
Read-only audit: true
```

Секреты должны храниться в `.env` и не должны попадать в Git, JSON-экспорт, screenshots или технические заключения.

---

## Основные интерфейсы

```text
http://SERVER_IP:8090/                         Unified Enterprise Admin
http://SERVER_IP:8090/#bitrixOneC              Аудит интеграции Bitrix24 ↔ 1С
http://SERVER_IP:8090/#management              Сводка руководителя
http://SERVER_IP:8090/integrator-diagnostics   Диагностика для интегратора
http://SERVER_IP:8090/digital-passport         Цифровой паспорт Bitrix24
http://SERVER_IP:8090/external-sources         Внешние источники и MCP
http://SERVER_IP:8090/system                    Состояние платформы
http://SERVER_IP:8090/about                     О системе
http://SERVER_IP:8090/about/meta                JSON-метаданные версии
```

На странице `#bitrixOneC` доступны:

- Платформа 5.0;
- Для руководства;
- Технический акт;
- Оценка;
- Pipeline;
- Сущности;
- Поля;
- Точки интеграции;
- Паспорт ERP;
- План проверки;
- Заключение.

---

## Требования

- Docker Engine;
- Docker Compose v2;
- доступ к коробочному Bitrix24;
- Bitrix24 REST webhook с правами только на необходимые методы;
- опубликованный HTTP-сервис `MCP_HTTPService` в 1С;
- бинарник `mcp-1c` внутри `browser-worker`;
- сетевой доступ контейнера к Bitrix24 и 1С;
- `jq` и `curl` для диагностики.

---

## Пример конфигурации

```env
BITRIX_WEBHOOK_URL=https://bitrix.example.kz/rest/USER_ID/SECRET/
BROWSER_BASE_URL=https://bitrix.example.kz
BROWSER_LOGIN=ai-audit
BROWSER_PASSWORD=change-me
BROWSER_HEADLESS=true
BROWSER_TIMEOUT_MS=45000
BROWSER_IGNORE_HTTPS_ERRORS=false

MCP_SERVERS_JSON='[{"id":"mcp_1c","name":"1C ERP","transport":"stdio","command":"/app/bin/mcp-1c","args":["--base","http://1c-server/base/hs/mcp-1c","--user","audit-user","--password","change-me","--quiet"],"timeout_seconds":120,"allowed_tools":["get_configuration_info","get_metadata_tree","get_object_structure","get_event_log","analyze_subsystems","validate_query","execute_query"]}]'

BITRIX_ONEC_ENTITY_MAP_JSON=[]
BITRIX_ONEC_FIELD_MAP_JSON=[]
BITRIX_ONEC_DATA_CHECKS_JSON=[]
```

Для production рекомендуется отдельная read-only учётная запись 1С и отдельный webhook Bitrix24 с минимально необходимыми правами.

---

## Установка и обновление

```bash
cd /opt/ai-bit

git fetch origin
git switch agent/frontend-stabilization-3.4.2
git pull

docker compose build --no-cache browser-worker
docker compose up -d --force-recreate browser-worker
```

Во время сборки должна появиться строка:

```text
Applied AI-BIT Enterprise 5.0.0 — Unified Integration Intelligence Platform
```

---

## Проверка версии

```bash
curl -sS http://127.0.0.1:8090/about/meta | jq
```

Ожидаем:

```json
{
  "product": "AI-BIT Enterprise",
  "version": "5.0.0"
}
```

---

## Запуск аудита интеграции

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/bitrix-onec-integration/collect \
  -o /tmp/bitrix-onec-500.json
```

Проверка нового ядра:

```bash
jq '.verification_pipeline.platform_v5' \
  /tmp/bitrix-onec-500.json
```

Краткая готовность движков:

```bash
jq '{
  version,
  status,
  readiness: .verification_pipeline.platform_v5.readiness,
  governance: .verification_pipeline.platform_v5.governance
}' /tmp/bitrix-onec-500.json
```

Evidence Engine 2.0:

```bash
jq '.verification_pipeline.platform_v5.engines.evidence' \
  /tmp/bitrix-onec-500.json
```

Data Quality:

```bash
jq '.verification_pipeline.platform_v5.engines.data_quality' \
  /tmp/bitrix-onec-500.json
```

Drift baseline:

```bash
jq '.verification_pipeline.platform_v5.engines.drift_detection' \
  /tmp/bitrix-onec-500.json
```

Business Impact:

```bash
jq '.verification_pipeline.platform_v5.engines.business_impact' \
  /tmp/bitrix-onec-500.json
```

Integrator Copilot:

```bash
jq '.verification_pipeline.platform_v5.engines.integrator_copilot' \
  /tmp/bitrix-onec-500.json
```

---

## Статусы и их смысл

| Статус | Значение |
|---|---|
| `confirmed` | Факт подтверждён evidence |
| `requires_additional_evidence` | Для вывода недостаточно данных |
| `not_confirmed` | Механизм не подтверждён, но его отсутствие не доказано |
| `configuration_required` | Необходимо настроить безопасную read-only проверку |
| `baseline_created` | Создана база для последующего drift comparison |
| `allowed` | Допуск к эксплуатации подтверждён |
| `allowed_with_restrictions` | Эксплуатация возможна после выполнения ограничений |
| `not_recommended` | Имеются подтверждённые блокирующие риски |
| `not_recommended_until_data_validation` | Архитектура изучена, но фактические данные ещё не сверены |

---

## Ограничения версии 5.0

- Data Quality Engine не выполняет произвольные запросы без явно разрешённых read-only правил.
- Drift Detection создаёт baseline; полноценная история изменений требует накопления нескольких снимков.
- Business Impact оценивает влияние только по подтверждённым findings.
- Copilot не выполняет изменения и не публикует код в Bitrix24 или 1С.
- Отраслевой benchmark не подменяется выдуманным сравнением с SAP, Oracle или Dynamics без проверяемой методологии.

---

## Дорожная карта

### 5.0.x

- стабилизация Unified Core;
- накопление drift snapshots;
- настройка read-only data checks;
- экспорт management conclusion и technical act;
- confidence calibration.

### 5.1

- фактическая сверка выборок;
- Data Quality Score по сущностям;
- duplicate and orphan detection;
- latency and freshness monitoring.

### 5.2

- история drift;
- уведомления о критических изменениях;
- сравнение архитектуры до/после релиза интегратора.

### 5.3

- интерактивное оспаривание finding;
- прикрепление дополнительного evidence;
- повторная оценка confidence;
- формализованная приёмка подрядчика.

---

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
© 2026. Все права защищены.
```
