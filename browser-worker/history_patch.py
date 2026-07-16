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
        "from fastapi import FastAPI, HTTPException, Query\nfrom fastapi.responses import HTMLResponse\n\nfrom dashboard import dashboard_html\nfrom deep_audit import analyze_deep_audit\nfrom history import CrawlHistory, diff_crawls\nfrom implementation_analysis import analyze_implementation\nfrom operational_intelligence import collect_operational_snapshot, read_latest_operational\nfrom operations_dashboard import operations_dashboard_html",
        "history imports",
    )

    text = text.replace(
        'FastAPI(title="AI-BIT Browser Worker", version="0.5.0")',
        'FastAPI(title="AI-BIT Browser Worker", version="0.9.0")',
    )
    text = text.replace('"version": "0.5.0"', '"version": "0.9.0"')

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
    endpoints = '''@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return dashboard_html()


@app.get("/operations", response_class=HTMLResponse)
async def operations_dashboard() -> str:
    return operations_dashboard_html()


@app.post("/operations/collect")
async def operations_collect() -> dict[str, Any]:
    try:
        return await collect_operational_snapshot(settings.browser_artifacts_dir)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/operations/latest")
async def operations_latest() -> dict[str, Any]:
    try:
        return read_latest_operational(settings.browser_artifacts_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No operational snapshot is available") from None


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
    print("Applied AI-BIT operational intelligence patch 0.9.0")


if __name__ == "__main__":
    main()
