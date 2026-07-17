# AI-BIT Enterprise

AI-BIT Enterprise — read-only платформа непрерывного технического, функционального, операционного и управленческого аудита коробочного Bitrix24.

## Текущая версия

Browser Worker: `2.0.0-alpha.7`.

## 2.0.0-alpha.7 — Management Conclusion

На странице руководителя появился обязательный текстовый блок **«Заключение AI-BIT»**. Он формируется встроенным Decision Engine и не зависит от Groq.

Главная ссылка остаётся прежней:

```text
http://SERVER_IP:8090/#management
```

Заключение отвечает на пять управленческих вопросов:

- что происходит;
- почему это происходит;
- чем это грозит компании;
- что необходимо утвердить руководству;
- какой эффект ожидается после исправления.

Пример логики:

```text
19% открытых задач просрочено
→ контроль исполнения недостаточен
→ сроки поручений продолжают смещаться
→ требуется еженедельный контроль и персональная ответственность руководителей
```

### Срок фактического внедрения

AI-BIT ищет наиболее раннюю подтверждённую дату рабочей активности в доступных системных артефактах:

- операционная статистика;
- Process Mining;
- Business Architecture;
- история crawl-снимков.

В заключении отображаются:

```text
Первые подтверждённые рабочие данные: ДД.ММ.ГГГГ
Наблюдаемый период: N дней
```

Система не подставляет произвольную дату. Если подтверждённая дата не найдена, срок внедрения не указывается.

### Структура заключения

- общий управленческий вывод;
- факты, на которых основан вывод;
- обязательные управленческие действия;
- последствия бездействия;
- ожидаемая экономия времени и денежных средств;
- период фактического использования системы.

## 2.0.0-alpha.6 — Resilient Executive Brief

Страница руководителя не зависит от Groq и не блокируется при недоступности внешнего AI-провайдера.

```text
открытие страницы
→ мгновенный показ последнего подтверждённого Executive Intelligence snapshot
→ фоновое обновление данных
→ автоматическая замена сводки после успешного расчёта
```

Groq используется только для дополнительного оформления подробного отчёта. Ошибка Groq не влияет на основной экран.

## Архитектура аудита

```text
Deep REST Evidence
→ Automatic Capability Discovery
→ Evidence-Based Audit
→ Knowledge Base & Methodology
→ Reference Model Audit
→ Executive Intelligence
→ Management Conclusion
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
  "version": "2.0.0-alpha.7",
  "product": "AI-BIT Enterprise",
  "developer": "Коваленко А.С.",
  "contact": "pizzakov@gmail.com"
}
```

## Проверка заключения

```bash
curl -sS -X POST \
  http://127.0.0.1:8090/executive-intelligence/collect \
  | jq '.management_conclusion'
```

Проверка срока наблюдения:

```bash
curl -sS \
  http://127.0.0.1:8090/executive-intelligence/latest \
  | jq '.management_conclusion.timeline'
```

## Разработчик

```text
Коваленко А.С.
pizzakov@gmail.com
```
