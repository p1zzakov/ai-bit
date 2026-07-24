FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY *.json ./

RUN python ./build_patch.py \
    && python ./crawler_patch.py \
    && python ./history_patch.py \
    && python ./rc_patch.py \
    && python ./branding_patch.py \
    && python ./management_report_patch.py \
    && python ./executive_intelligence_patch.py \
    && python ./management_intelligence_patch.py \
    && python ./management_report_enrichment_patch.py \
    && python ./executive_brief_patch.py \
    && python ./mandatory_processes_patch.py \
    && python ./reference_model_patch.py \
    && python ./capability_discovery_patch.py \
    && python ./evidence_audit_patch.py \
    && python ./deep_rest_patch.py \
    && python ./knowledge_base_patch.py \
    && python ./management_brief_v2_patch.py \
    && python ./management_conclusion_patch.py \
    && python ./business_value_patch.py \
    && python ./business_value_advanced_patch.py \
    && python ./executive_kpi_patch.py \
    && python ./transformation_intelligence_patch.py \
    && python ./process_optimizer_patch.py \
    && python ./release_210_patch.py \
    && python ./release_220_patch.py \
    && python ./release_300_patch.py \
    && python ./release_310_patch.py \
    && python ./release_320_patch.py \
    && python ./release_321_patch.py \
    && python ./release_340_patch.py \
    && python -m compileall -q /app

RUN mkdir -p \
    /app/artifacts \
    /app/artifacts/history \
    /app/artifacts/operations \
    /app/artifacts/knowledge-graph \
    /app/artifacts/process-mining \
    /app/artifacts/business-architecture \
    /app/artifacts/reports \
    /app/artifacts/management-reports \
    /app/artifacts/executive-intelligence \
    /app/artifacts/reference-audit \
    /app/artifacts/capability-discovery \
    /app/artifacts/evidence-audit \
    /app/artifacts/deep-rest-evidence \
    /app/artifacts/scheduler \
    /app/state

EXPOSE 8090
CMD ["uvicorn", "integrated_app:app", "--host", "0.0.0.0", "--port", "8090"]
