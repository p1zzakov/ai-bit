# AI-BIT Enterprise 3.3.0

## Evidence-Based Executive Decision Intelligence

Релиз добавляет четыре управленческих компонента без новых финансовых и прогнозных допущений.

### AI CIO Recommendations

- решения формируются по подтверждённым рискам, Root Cause Analysis и Roadmap;
- для каждого решения указываются основание, действие, ответственная роль, срок и уверенность;
- денежный эффект и неподтверждённые предположения исключены.

### Department Operational Maturity

- рейтинг подразделений строится по подтверждённым данным задач Bitrix24;
- учитываются просрочка, задачи без срока и концентрация риска;
- показатель не является оценкой ценности сотрудника или общей эффективности подразделения.

### AI Timeline

- динамика строится только по сохранённым снимкам Executive Intelligence;
- отображаются изменения цифровой зрелости, покрытия эталонной модели, просрочки и задач без срока;
- линейные прогнозы и финансовые оценки в блок не включаются.

### Executive Score

- единый индекс от 0 до 100;
- прозрачные веса компонентов;
- целевой уровень 80;
- отображаются текущий балл, grade, разрыв до цели и покрытие расчёта.

## Интерфейс

Подробные блоки размещены в `/#intelligence`. На странице `/#management` показывается только Executive Score и краткая управленческая сводка.

## Обновление

```bash
cd /opt/ai-bit
git pull
docker compose build --no-cache browser-worker
docker compose up -d browser-worker
```

## Проверка

```bash
curl -sS -X POST http://127.0.0.1:8090/executive-intelligence/collect -o /tmp/executive-3.3.0.json
jq '{executive_score, department_maturity, ai_timeline, ai_cio}' /tmp/executive-3.3.0.json
```
