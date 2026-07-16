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
        "from ai_provider import ai_status, generate_advice\nfrom admin_dashboard import admin_dashboard_html\nfrom business_architecture import collect_business_architecture, read_latest_business_architecture\nfrom business_architecture_dashboard import business_architecture_dashboard_html\nfrom system_dashboard import system_dashboard_html\nfrom system_health import build_system_health",
        "rc imports",
    )
    text = text.replace('version="1.0.0-beta.2"', 'version="1.0.0-rc.3"')
    text = text.replace('"version": "1.0.0-beta.2"', '"version": "1.0.0-rc.3"')

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


@app.get("/system", response_class=HTMLResponse)
async def system_dashboard() -> str:
    return system_dashboard_html()


@app.get("/system/health")
async def system_health() -> dict[str, Any]:
    return await build_system_health(
        settings.browser_artifacts_dir,
        CRAWL_HISTORY,
        settings.browser_base_url,
    )
'''
    text = replace_once(text, marker, addition, "business architecture and system endpoints")

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
    print("Applied AI-BIT System Health patch 1.0.0-rc.3")


if __name__ == "__main__":
    main()
