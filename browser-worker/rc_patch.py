from __future__ import annotations

from pathlib import Path

APP_PATH = Path("/app/app.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Patch {label!r} expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from ai_provider import ai_status, generate_advice",
        "from ai_provider import ai_status, generate_advice\nfrom fastapi.responses import FileResponse\nfrom admin_dashboard import admin_dashboard_html\nfrom automation_dashboard import automation_dashboard_html\nfrom branding import about_page_html, brand_integrity, install_branding, product_metadata\nfrom business_architecture import collect_business_architecture, read_latest_business_architecture\nfrom business_architecture_dashboard import business_architecture_dashboard_html\nfrom report_engine import generate_report, list_reports, report_file\nfrom reports_dashboard import reports_dashboard_html\nfrom scheduler_engine import SchedulerService\nfrom system_dashboard import system_dashboard_html\nfrom system_health import build_system_health",
        "rc imports",
    )
    text = text.replace('version="1.0.0-beta.2"', 'version="1.0.0-rc.7"')
    text = text.replace('"version": "1.0.0-beta.2"', '"version": "1.0.0-rc.7"')

    app_marker = 'app = FastAPI(title="AI-BIT Browser Worker", version="1.0.0-rc.7")\n'
    text = replace_once(
        text,
        app_marker,
        app_marker + 'install_branding(app)\n',
        "branding middleware",
    )

    history_marker = 'CRAWL_HISTORY = CrawlHistory(Path("/app/artifacts/history"))\n'
    text = replace_once(
        text,
        history_marker,
        history_marker + 'SCHEDULER = SchedulerService(settings.browser_artifacts_dir)\n',
        "scheduler service",
    )

    health_marker = '''@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "AI-BIT Browser Worker",
        "version": "1.0.0-rc.7",
        "configured": bool(settings.browser_base_url),
        "session_saved": settings.browser_state_file.exists(),
    }
'''
    health_replacement = '''@app.get("/health")
async def health() -> dict[str, Any]:
    result = {
        "status": "ok",
        "service": "AI-BIT Browser Worker",
        "version": "1.0.0-rc.7",
        "configured": bool(settings.browser_base_url),
        "session_saved": settings.browser_state_file.exists(),
    }
    result.update({
        "product": "AI-BIT Enterprise",
        "developer": "Коваленко А.С.",
        "contact": "pizzakov@gmail.com",
        "brand_integrity": brand_integrity(),
    })
    return result
'''
    text = replace_once(text, health_marker, health_replacement, "health branding metadata")

    root_marker = '''@app.get("/", response_class=HTMLResponse)
async def executive_root() -> str:
    return executive_dashboard_html()
'''
    root_replacement = '''@app.get("/", response_class=HTMLResponse)
async def admin_root() -> str:
    return admin_dashboard_html()


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard() -> str:
    return admin_dashboard_html()
'''
    text = replace_once(text, root_marker, root_replacement, "unified admin root")

    marker = '''@app.get("/processes", response_class=HTMLResponse)
async def process_dashboard() -> str:
    return process_dashboard_html()
'''
    addition = marker + '''

@app.on_event("startup")
async def scheduler_startup() -> None:
    await SCHEDULER.start()


@app.on_event("shutdown")
async def scheduler_shutdown() -> None:
    await SCHEDULER.stop()


@app.get("/automation", response_class=HTMLResponse)
async def automation_dashboard() -> str:
    return automation_dashboard_html()


@app.get("/scheduler/status")
async def scheduler_status() -> dict[str, Any]:
    return SCHEDULER.status()


@app.post("/scheduler/run/{job_name}")
async def scheduler_run(job_name: str) -> dict[str, Any]:
    try:
        return await SCHEDULER.run(job_name, trigger="manual")
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown scheduler job") from None
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/about", response_class=HTMLResponse)
async def about_page() -> str:
    return about_page_html("1.0.0-rc.7")


@app.get("/about/meta")
async def about_metadata() -> dict[str, Any]:
    return product_metadata("1.0.0-rc.7")


@app.get("/business-architecture", response_class=HTMLResponse)
async def business_architecture_dashboard() -> str:
    return business_architecture_dashboard_html()


@app.post("/business-architecture/collect")
async def business_architecture_collect() -> dict[str, Any]:
    operations = None
    crawl = None
    try:
        operations = read_latest_operational(settings.browser_artifacts_dir)
    except FileNotFoundError:
        pass
    try:
        crawl = CRAWL_HISTORY.latest()
    except FileNotFoundError:
        pass
    try:
        return await collect_business_architecture(settings.browser_artifacts_dir, operations=operations, crawl=crawl)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/business-architecture/latest")
async def business_architecture_latest() -> dict[str, Any]:
    try:
        return read_latest_business_architecture(settings.browser_artifacts_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No business architecture audit is available") from None


@app.get("/reports-ui", response_class=HTMLResponse)
async def reports_ui() -> str:
    return reports_dashboard_html()


@app.get("/reports")
async def reports_list(limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    return list_reports(settings.browser_artifacts_dir, limit=limit)


@app.post("/reports/generate")
async def reports_generate() -> dict[str, Any]:
    try:
        return await generate_report(settings.browser_artifacts_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc


@app.get("/reports/{report_id}/{fmt}")
async def reports_download(report_id: str, fmt: str):
    try:
        path = report_file(settings.browser_artifacts_dir, report_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found") from None
    media = {"json": "application/json", "html": "text/html; charset=utf-8", "pdf": "application/pdf"}[fmt]
    return FileResponse(path, media_type=media, filename=path.name)


@app.get("/system", response_class=HTMLResponse)
async def system_dashboard() -> str:
    return system_dashboard_html()


@app.get("/system/health")
async def system_health() -> dict[str, Any]:
    result = await build_system_health(
        settings.browser_artifacts_dir,
        CRAWL_HISTORY,
        settings.browser_base_url,
    )
    result["brand_integrity"] = brand_integrity()
    result["developer"] = {
        "name": "Коваленко А.С.",
        "email": "pizzakov@gmail.com",
    }
    if result["brand_integrity"]["status"] != "ok":
        result["overall_status"] = "warning"
        result.setdefault("recommendations", []).append({
            "severity": "warning",
            "title": "Нарушена целостность обязательной подписи разработчика",
            "action": "Проверить branding.py и восстановить централизованный компонент attribution.",
        })
    return result
'''
    text = replace_once(text, marker, addition, "branding automation business architecture reports and system endpoints")

    graph_line = '    graph = build_unified_graph(crawl, operations)\n    compact_context = {'
    graph_replacement = '''    graph = build_unified_graph(crawl, operations)
    business_architecture = None
    try:
        business_architecture = read_latest_business_architecture(settings.browser_artifacts_dir)
    except FileNotFoundError:
        pass
    compact_context = {'''
    text = replace_once(text, graph_line, graph_replacement, "AI business architecture context setup")

    context_marker = '''        "process_mining": {
            "summary": (process_mining or {}).get("summary", {}),
            "automation_candidates": (process_mining or {}).get("automation_candidates", [])[:15],
            "handoff_routes": (process_mining or {}).get("handoff_routes", [])[:10],
            "bottlenecks": (process_mining or {}).get("bottlenecks", [])[:10],
        },
'''
    context_addition = context_marker + '''        "business_architecture": {
            "enterprise_health": (business_architecture or {}).get("enterprise_health"),
            "summary": (business_architecture or {}).get("summary", {}),
            "domains": {
                key: {
                    "score": value.get("score"),
                    "status": value.get("status"),
                    "evidence_status": value.get("evidence_status"),
                    "scores": value.get("scores", {}),
                    "summary": value.get("summary", {}),
                    "recommendations": value.get("recommendations", [])[:10],
                }
                for key, value in (business_architecture or {}).get("domains", {}).items()
            },
            "recommendations": (business_architecture or {}).get("recommendations", [])[:20],
        },
'''
    text = replace_once(text, context_marker, context_addition, "AI business architecture context")

    APP_PATH.write_text(text, encoding="utf-8")
    print("Applied AI-BIT Brand Integrity patch 1.0.0-rc.7")


if __name__ == "__main__":
    main()
