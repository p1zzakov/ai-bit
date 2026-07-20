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
        "from pydantic_settings import BaseSettings, SettingsConfigDict",
        "from pydantic_settings import BaseSettings, SettingsConfigDict\n\nfrom crawler import CrawlRequest, crawl_portal",
        "crawler import",
    )
    text = text.replace(
        'FastAPI(title="AI-BIT Browser Worker", version="0.4.0")',
        'FastAPI(title="AI-BIT Browser Worker", version="0.5.0")',
    )
    text = text.replace('"version": "0.4.0"', '"version": "0.5.0"')

    marker = '''@app.post("/scan/all")
async def scan_all() -> dict[str, Any]:
'''
    endpoints = '''@app.post("/crawl")
async def crawl(request: CrawlRequest) -> dict[str, Any]:
    """Discover same-origin Bitrix24 pages and build a navigable portal map."""
    ensure_configured()
    return await crawl_portal(
        request,
        base_url=settings.browser_base_url,
        artifacts_dir=settings.browser_artifacts_dir,
        new_context=new_context,
        is_authenticated=is_authenticated,
        login=login,
        navigate_page=navigate_page,
    )


@app.get("/crawl/latest")
async def latest_crawl() -> dict[str, Any]:
    latest_path = settings.browser_artifacts_dir / "latest-crawl.json"
    if not latest_path.exists():
        raise HTTPException(status_code=404, detail="No crawl result is available")
    return json.loads(latest_path.read_text(encoding="utf-8"))


'''
    if marker not in text:
        raise RuntimeError("scan_all endpoint marker not found")
    text = text.replace(marker, endpoints + marker, 1)

    APP_PATH.write_text(text, encoding="utf-8")
    print("Applied AI-BIT crawler patch 0.5.0")


if __name__ == "__main__":
    main()
