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
COPY management_report.py ./management_report.py
COPY management_report_dashboard.py ./management_report_dashboard.py
COPY management_brief_dashboard_v2.py ./management_brief_dashboard_v2.py
COPY management_compact.py ./management_compact.py
COPY executive_portals.py ./executive_portals.py
COPY management_conclusion.py ./management_conclusion.py
COPY business_value.py ./business_value.py
COPY executive_kpi.py ./executive_kpi.py
COPY transformation_intelligence.py ./transformation_intelligence.py
COPY process_optimizer.py ./process_optimizer.py
COPY release_manifest.py ./release_manifest.py
COPY executive_intelligence.py ./executive_intelligence.py
COPY executive_intelligence_dashboard.py ./executive_intelligence_dashboard.py
COPY reference_model.py ./reference_model.py
COPY reference_models.json ./reference_models.json
COPY capability_discovery.py ./capability_discovery.py
COPY evidence_engine.py ./evidence_engine.py
COPY evidence_methodology.json ./evidence_methodology.json
COPY deep_rest_evidence.py ./deep_rest_evidence.py
COPY knowledge_base.py ./knowledge_base.py
COPY knowledge_catalog.json ./knowledge_catalog.json
COPY scheduler_engine.py ./scheduler_engine.py
COPY automation_dashboard.py ./automation_dashboard.py
COPY integrator_diagnostics.py ./integrator_diagnostics.py
COPY integrator_dashboard.py ./integrator_dashboard.py
COPY implementation_blueprint.py ./implementation_blueprint.py
COPY source_provider.py ./source_provider.py
COPY external_sources_dashboard.py ./external_sources_dashboard.py
COPY bitrix_onec_integration_audit.py ./bitrix_onec_integration_audit.py
COPY bitrix_onec_integration_dashboard.py ./bitrix_onec_integration_dashboard.py
COPY onec_mcp_parser.py ./onec_mcp_parser.py
COPY integration_verification_pipeline.py ./integration_verification_pipeline.py
COPY branding.py ./branding.py
COPY unified_graph.py ./unified_graph.py
COPY ai_provider.py ./ai_provider.py
COPY build_patch.py ./build_patch.py
COPY crawler_patch.py ./crawler_patch.py
COPY history_patch.py ./history_patch.py
COPY rc_patch.py ./rc_patch.py
COPY branding_patch.py ./branding_patch.py
COPY management_report_patch.py ./management_report_patch.py
COPY executive_intelligence_patch.py ./executive_intelligence_patch.py
COPY management_intelligence_patch.py ./management_intelligence_patch.py
COPY management_report_enrichment_patch.py ./management_report_enrichment_patch.py
COPY executive_brief_patch.py ./executive_brief_patch.py
COPY mandatory_processes_patch.py ./mandatory_processes_patch.py
COPY reference_model_patch.py ./reference_model_patch.py
COPY capability_discovery_patch.py ./capability_discovery_patch.py
COPY evidence_audit_patch.py ./evidence_audit_patch.py
COPY deep_rest_patch.py ./deep_rest_patch.py
COPY knowledge_base_patch.py ./knowledge_base_patch.py
COPY management_brief_v2_patch.py ./management_brief_v2_patch.py
COPY management_conclusion_patch.py ./management_conclusion_patch.py
COPY business_value_patch.py ./business_value_patch.py
COPY business_value_advanced_patch.py ./business_value_advanced_patch.py
COPY executive_kpi_patch.py ./executive_kpi_patch.py
COPY transformation_intelligence_patch.py ./transformation_intelligence_patch.py
COPY process_optimizer_patch.py ./process_optimizer_patch.py
COPY release_210_patch.py ./release_210_patch.py
COPY release_220_patch.py ./release_220_patch.py
COPY release_300_patch.py ./release_300_patch.py
COPY release_310_patch.py ./release_310_patch.py
COPY release_320_patch.py ./release_320_patch.py
COPY release_321_patch.py ./release_321_patch.py
COPY release_340_patch.py ./release_340_patch.py
COPY release_342_patch.py ./release_342_patch.py
COPY release_350_patch.py ./release_350_patch.py
COPY release_351_patch.py ./release_351_patch.py
COPY release_360_patch.py ./release_360_patch.py
COPY release_361_patch.py ./release_361_patch.py
COPY release_430_patch.py ./release_430_patch.py
COPY release_431_patch.py ./release_431_patch.py
COPY release_432_patch.py ./release_432_patch.py
COPY release_433_patch.py ./release_433_patch.py
COPY release_440_patch.py ./release_440_patch.py
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
    && python ./release_342_patch.py \
    && python ./release_350_patch.py \
    && python ./release_351_patch.py \
    && python ./release_360_patch.py \
    && python ./release_361_patch.py \
    && python ./release_430_patch.py \
    && python ./release_431_patch.py \
    && python ./release_432_patch.py \
    && python ./release_433_patch.py \
    && python ./release_440_patch.py \
    && python -m py_compile ./app.py ./login_debug.py ./crawler.py ./history.py ./dashboard.py ./implementation_analysis.py ./deep_audit.py ./operational_intelligence.py ./operational_trends.py ./operations_dashboard.py ./executive_dashboard.py ./process_mining.py ./process_dashboard.py ./business_architecture.py ./business_architecture_dashboard.py ./admin_dashboard.py ./system_health.py ./system_dashboard.py ./report_engine.py ./reports_dashboard.py ./management_report.py ./management_report_dashboard.py ./management_brief_dashboard_v2.py ./management_compact.py ./executive_portals.py ./management_conclusion.py ./business_value.py ./executive_kpi.py ./transformation_intelligence.py ./process_optimizer.py ./release_manifest.py ./executive_intelligence.py ./executive_intelligence_dashboard.py ./reference_model.py ./capability_discovery.py ./evidence_engine.py ./deep_rest_evidence.py ./knowledge_base.py ./scheduler_engine.py ./automation_dashboard.py ./integrator_diagnostics.py ./integrator_dashboard.py ./implementation_blueprint.py ./source_provider.py ./external_sources_dashboard.py ./bitrix_onec_integration_audit.py ./bitrix_onec_integration_dashboard.py ./onec_mcp_parser.py ./integration_verification_pipeline.py ./branding.py ./branding_patch.py ./management_report_patch.py ./executive_intelligence_patch.py ./management_intelligence_patch.py ./management_report_enrichment_patch.py ./executive_brief_patch.py ./mandatory_processes_patch.py ./reference_model_patch.py ./capability_discovery_patch.py ./evidence_audit_patch.py ./deep_rest_patch.py ./knowledge_base_patch.py ./management_brief_v2_patch.py ./management_conclusion_patch.py ./business_value_patch.py ./business_value_advanced_patch.py ./executive_kpi_patch.py ./transformation_intelligence_patch.py ./process_optimizer_patch.py ./release_210_patch.py ./release_220_patch.py ./release_300_patch.py ./release_310_patch.py ./release_320_patch.py ./release_321_patch.py ./release_340_patch.py ./release_342_patch.py ./release_350_patch.py ./release_351_patch.py ./release_360_patch.py ./release_361_patch.py ./release_430_patch.py ./release_431_patch.py ./release_432_patch.py ./release_433_patch.py ./release_440_patch.py ./unified_graph.py ./ai_provider.py
RUN mkdir -p /app/artifacts /app/artifacts/history /app/artifacts/operations /app/artifacts/knowledge-graph /app/artifacts/process-mining /app/artifacts/business-architecture /app/artifacts/reports /app/artifacts/management-reports /app/artifacts/executive-intelligence /app/artifacts/reference-audit /app/artifacts/capability-discovery /app/artifacts/evidence-audit /app/artifacts/deep-rest-evidence /app/artifacts/external-sources /app/artifacts/bitrix-onec-integration /app/artifacts/scheduler /app/state /app/bin

EXPOSE 8090
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
