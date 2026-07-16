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
        "from fastapi import FastAPI, HTTPException",
        "from fastapi import FastAPI, HTTPException, Query\nfrom fastapi.responses import HTMLResponse\n\nfrom ai_provider import ai_status, generate_advice\nfrom dashboard import dashboard_html\nfrom deep_audit import analyze_deep_audit\nfrom executive_dashboard import executive_dashboard_html\nfrom history import CrawlHistory, diff_crawls\nfrom implementation_analysis import analyze_implementation\nfrom operational_intelligence import collect_operational_snapshot, read_latest_operational\nfrom operational_trends import build_operational_trends, list_operational_snapshots\nfrom operations_dashboard import operations_dashboard_html\nfrom process_dashboard import process_dashboard_html\nfrom process_mining import analyze_process_mining, save_process_mining\nfrom unified_graph import build_unified_graph, save_unified_graph",
        "history imports",
    )

    text = text.replace(
        'FastAPI(title="AI-BIT Browser Worker", version="0.5.0")',
        'FastAPI(title="AI-BIT Browser Worker", version="1.0.0-beta.2")',
    )
    text = text.replace('"version": "0.5.0"', '"version": "1.0.0-beta.2"')

    settings_marker = "settings = Settings()\n"
    text = replace_once(
        text,
        settings_marker,
        settings_marker + 'CRAWL_HISTORY = CrawlHistory(Path("/app/artifacts/history"))\n',
        "history store",
    )

    old_crawl = '''    return await crawl_portal(
        request,
        base_url=settings.browser_base_url,
        artifacts_dir=settings.browser_artifacts_dir,
        new_context=new_context,
        is_authenticated=is_authenticated,
        login=login,
        navigate_page=navigate_page,
    )
'''
    new_crawl = '''    result = await crawl_portal(
        request,
        base_url=settings.browser_base_url,
        artifacts_dir=settings.browser_artifacts_dir,
        new_context=new_context,
        is_authenticated=is_authenticated,
        login=login,
        navigate_page=navigate_page,
    )
    result["assessment"] = analyze_implementation(result)
    result["deep_audit"] = analyze_deep_audit(result)
    history_path = CRAWL_HISTORY.save(result)
    result["history_id"] = history_path.stem
    result["history_path"] = str(history_path)
    return result
'''
    text = replace_once(text, old_crawl, new_crawl, "persist crawl history")

    marker = '''@app.get("/crawl/latest")
async def latest_crawl() -> dict[str, Any]:
'''
    endpoints = '''@app.get("/", response_class=HTMLResponse)
async def executive_root() -> str:
    return executive_dashboard_html()


@app.get("/executive", response_class=HTMLResponse)
async def executive_dashboard() -> str:
    return executive_dashboard_html()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return dashboard_html()


@app.get("/operations", response_class=HTMLResponse)
async def operations_dashboard() -> str:
    return operations_dashboard_html()


@app.get("/processes", response_class=HTMLResponse)
async def process_dashboard() -> str:
    return process_dashboard_html()


@app.post("/operations/collect")
async def operations_collect() -> dict[str, Any]:
    try:
        result = await collect_operational_snapshot(settings.browser_artifacts_dir)
        process_result = analyze_process_mining(result)
        process_result["artifact"] = str(save_process_mining(settings.browser_artifacts_dir, process_result))
        result["process_mining_summary"] = process_result.get("summary", {})
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/operations/latest")
async def operations_latest() -> dict[str, Any]:
    try:
        return read_latest_operational(settings.browser_artifacts_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No operational snapshot is available") from None


@app.get("/operations/history")
async def operations_history(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    items = list_operational_snapshots(settings.browser_artifacts_dir, limit=limit)
    return [{"id": item["id"], "generated_at": item["generated_at"], "summary": item["summary"]} for item in items]


@app.get("/operations/trends")
async def operations_trends(days: int = Query(default=30)) -> dict[str, Any]:
    try:
        return build_operational_trends(settings.browser_artifacts_dir, days=days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No operational snapshots are available") from None


@app.get("/process-mining/latest")
async def process_mining_latest() -> dict[str, Any]:
    try:
        operations = read_latest_operational(settings.browser_artifacts_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No operational snapshot is available") from None
    result = analyze_process_mining(operations)
    result["artifact"] = str(save_process_mining(settings.browser_artifacts_dir, result))
    return result


@app.get("/knowledge-graph/latest")
async def knowledge_graph_latest() -> dict[str, Any]:
    crawl = None
    operations = None
    try:
        crawl = CRAWL_HISTORY.latest()
    except FileNotFoundError:
        pass
    try:
        operations = read_latest_operational(settings.browser_artifacts_dir)
    except FileNotFoundError:
        pass
    if crawl is None and operations is None:
        raise HTTPException(status_code=404, detail="No audit data is available")
    graph = build_unified_graph(crawl, operations)
    graph["artifact"] = str(save_unified_graph(settings.browser_artifacts_dir, graph))
    return graph


@app.get("/ai/status")
async def get_ai_status() -> dict[str, Any]:
    return ai_status()


@app.post("/ai/advice")
async def ai_advice(question: str = Query(default="Сформируй приоритетный план улучшения внедрения Bitrix24")) -> dict[str, Any]:
    crawl = None
    operations = None
    trends = None
    process_mining = None
    try:
        crawl = CRAWL_HISTORY.latest()
    except FileNotFoundError:
        pass
    try:
        operations = read_latest_operational(settings.browser_artifacts_dir)
    except FileNotFoundError:
        pass
    try:
        trends = build_operational_trends(settings.browser_artifacts_dir, days=30)
    except (FileNotFoundError, ValueError):
        pass
    if operations:
        process_mining = analyze_process_mining(operations)
    graph = build_unified_graph(crawl, operations)
    compact_context = {
        "graph_summary": graph.get("summary"),
        "recommendations": graph.get("recommendations", [])[:50],
        "operations_summary": (operations or {}).get("summary", {}),
        "operations_trend_30d": {
            "status": (trends or {}).get("status"),
            "direction": (trends or {}).get("direction"),
            "actual_comparison_days": (trends or {}).get("actual_comparison_days"),
            "deltas": (trends or {}).get("deltas", {}),
            "worsened_employees": (trends or {}).get("employees", {}).get("worsened", [])[:10],
            "worsened_departments": (trends or {}).get("departments", {}).get("worsened", [])[:10],
        },
        "process_mining": {
            "summary": (process_mining or {}).get("summary", {}),
            "automation_candidates": (process_mining or {}).get("automation_candidates", [])[:15],
            "handoff_routes": (process_mining or {}).get("handoff_routes", [])[:10],
            "bottlenecks": (process_mining or {}).get("bottlenecks", [])[:10],
        },
        "implementation": (crawl or {}).get("assessment", {}),
        "deep_audit_summary": (crawl or {}).get("deep_audit", {}).get("summary", {}),
    }
    try:
        return generate_advice(compact_context, question)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/crawl/history")
async def crawl_history(limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    return CRAWL_HISTORY.list(limit=limit)


@app.get("/crawl/history/{audit_id}")
async def crawl_history_item(audit_id: str) -> dict[str, Any]:
    try:
        return CRAWL_HISTORY.read(audit_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Crawl audit not found") from None


@app.get("/crawl/assessment/latest")
async def latest_assessment() -> dict[str, Any]:
    items = CRAWL_HISTORY.list(limit=1)
    if not items:
        raise HTTPException(status_code=404, detail="No crawl audit is available")
    crawl = CRAWL_HISTORY.read(str(items[0]["id"]))
    return analyze_implementation(crawl)


@app.get("/crawl/assessment/{audit_id}")
async def crawl_assessment(audit_id: str) -> dict[str, Any]:
    try:
        crawl = CRAWL_HISTORY.read(audit_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Crawl audit not found") from None
    return analyze_implementation(crawl)


@app.get("/crawl/deep-audit/latest")
async def latest_deep_audit() -> dict[str, Any]:
    items = CRAWL_HISTORY.list(limit=1)
    if not items:
        raise HTTPException(status_code=404, detail="No crawl audit is available")
    crawl = CRAWL_HISTORY.read(str(items[0]["id"]))
    return analyze_deep_audit(crawl)


@app.get("/crawl/deep-audit/{audit_id}")
async def crawl_deep_audit(audit_id: str) -> dict[str, Any]:
    try:
        crawl = CRAWL_HISTORY.read(audit_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Crawl audit not found") from None
    return analyze_deep_audit(crawl)


@app.get("/crawl/diff")
async def crawl_diff(before: str, after: str) -> dict[str, Any]:
    try:
        previous = CRAWL_HISTORY.read(before)
        current = CRAWL_HISTORY.read(after)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Crawl audit not found: {exc}") from None
    return diff_crawls(previous, current)


'''
    if marker not in text:
        raise RuntimeError("crawl latest endpoint marker not found")
    text = text.replace(marker, endpoints + marker, 1)

    APP_PATH.write_text(text, encoding="utf-8")
    print("Applied AI-BIT process mining patch 1.0.0-beta.2")


if __name__ == "__main__":
    main()
