FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY login_debug.py ./login_debug.py
COPY presets.json ./presets.json
COPY crawler.py ./crawler.py
COPY history.py ./history.py
COPY dashboard.py ./dashboard.py
COPY implementation_analysis.py ./implementation_analysis.py
COPY deep_audit.py ./deep_audit.py
COPY operational_intelligence.py ./operational_intelligence.py
COPY operational_trends.py ./operational_trends.py
COPY operations_dashboard.py ./operations_dashboard.py
COPY executive_dashboard.py ./executive_dashboard.py
COPY process_mining.py ./process_mining.py
COPY process_dashboard.py ./process_dashboard.py
COPY business_architecture.py ./business_architecture.py
COPY business_architecture_dashboard.py ./business_architecture_dashboard.py
COPY admin_dashboard.py ./admin_dashboard.py
COPY system_health.py ./system_health.py
COPY system_dashboard.py ./system_dashboard.py
COPY report_engine.py ./report_engine.py
COPY reports_dashboard.py ./reports_dashboard.py
COPY scheduler_engine.py ./scheduler_engine.py
COPY automation_dashboard.py ./automation_dashboard.py
COPY branding.py ./branding.py
COPY unified_graph.py ./unified_graph.py
COPY ai_provider.py ./ai_provider.py
COPY build_patch.py ./build_patch.py
COPY crawler_patch.py ./crawler_patch.py
COPY history_patch.py ./history_patch.py
COPY rc_patch.py ./rc_patch.py
RUN python ./build_patch.py \
    && python ./crawler_patch.py \
    && python ./history_patch.py \
    && python ./rc_patch.py \
    && python -m py_compile ./app.py ./login_debug.py ./crawler.py ./history.py ./dashboard.py ./implementation_analysis.py ./deep_audit.py ./operational_intelligence.py ./operational_trends.py ./operations_dashboard.py ./executive_dashboard.py ./process_mining.py ./process_dashboard.py ./business_architecture.py ./business_architecture_dashboard.py ./admin_dashboard.py ./system_health.py ./system_dashboard.py ./report_engine.py ./reports_dashboard.py ./scheduler_engine.py ./automation_dashboard.py ./branding.py ./unified_graph.py ./ai_provider.py
RUN mkdir -p /app/artifacts /app/artifacts/history /app/artifacts/operations /app/artifacts/knowledge-graph /app/artifacts/process-mining /app/artifacts/business-architecture /app/artifacts/reports /app/artifacts/scheduler /app/state

EXPOSE 8090
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
