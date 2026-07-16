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
        'app = FastAPI(title="AI-BIT Browser Worker", version="0.2.0")',
        'app = FastAPI(title="AI-BIT Browser Worker", version="0.3.0")',
        "application version",
    )
    text = replace_once(
        text,
        '    "contact_center": "/contact_center/",',
        '    "contact_center": "/services/contact_center/",',
        "contact center preset",
    )

    marker = "\n\nasync def collect_page(\n"
    helpers = '''\n\ndef classify_page_status(navigation: dict[str, Any], target_url: str, final_url: str) -> str:\n    http_status = navigation.get("http_status")\n    if http_status in (401, 403):\n        return "denied"\n    if http_status == 404:\n        return "not_found"\n    if navigation.get("status") == "error":\n        return "error"\n    if navigation.get("timed_out"):\n        return "partial"\n    if navigation.get("request_failures") or navigation.get("http_errors"):\n        return "partial"\n    if final_url.rstrip("/") != target_url.rstrip("/"):\n        return "redirected"\n    return "ok"\n\n\nasync def safe_title(page: Page) -> tuple[str, str | None]:\n    try:\n        return await page.title(), None\n    except PlaywrightError as exc:\n        return "", str(exc)\n\n\nasync def safe_inner_texts(page: Page, selector: str) -> tuple[list[str], str | None]:\n    try:\n        return await page.locator(selector).all_inner_texts(timeout=10000), None\n    except PlaywrightError as exc:\n        return [], str(exc)\n\n\nasync def safe_links(page: Page) -> tuple[list[dict[str, str]], str | None]:\n    try:\n        links = await page.locator("a[href]").evaluate_all(\n            "els => els.slice(0,500).map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text || x.href)"\n        )\n        return links, None\n    except PlaywrightError as exc:\n        return [], str(exc)\n\n\nasync def safe_body_text(page: Page) -> tuple[str, str | None]:\n    try:\n        text = await page.locator("body").inner_text(timeout=10000)\n        return text, None\n    except PlaywrightError as exc:\n        try:\n            text = await page.locator("html").inner_text(timeout=5000)\n            return text, f"body unavailable: {exc}"\n        except PlaywrightError as fallback_exc:\n            return "", f"body unavailable: {exc}; html fallback failed: {fallback_exc}"\n'''
    if marker not in text:
        raise RuntimeError("collect_page marker not found")
    text = text.replace(marker, helpers + marker, 1)

    old_collection = '''    html_content = await page.content()\n    html_path.write_text(html_content, encoding="utf-8")\n    title = await page.title()\n    headings = await page.locator("h1, h2, h3").all_inner_texts()\n    menu_text = await page.locator(\n        "nav, aside, [class*=menu], [class*=sidebar], [class*=navigation]"\n    ).all_inner_texts()\n    links = await page.locator("a[href]").evaluate_all(\n        "els => els.slice(0,500).map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text || x.href)"\n    )\n    body_text = await page.locator("body").inner_text()\n    compact_text = re.sub(r"\\s+", " ", body_text).strip()[:50000]\n'''
    new_collection = '''    extraction_errors: dict[str, str] = {}\n    try:\n        html_content = await page.content()\n    except PlaywrightError as exc:\n        html_content = ""\n        extraction_errors["html"] = str(exc)\n    html_path.write_text(html_content, encoding="utf-8")\n\n    title, error = await safe_title(page)\n    if error:\n        extraction_errors["title"] = error\n    headings, error = await safe_inner_texts(page, "h1, h2, h3")\n    if error:\n        extraction_errors["headings"] = error\n    menu_text, error = await safe_inner_texts(\n        page, "nav, aside, [class*=menu], [class*=sidebar], [class*=navigation]"\n    )\n    if error:\n        extraction_errors["menu_text"] = error\n    links, error = await safe_links(page)\n    if error:\n        extraction_errors["links"] = error\n    body_text, error = await safe_body_text(page)\n    if error:\n        extraction_errors["visible_text"] = error\n    compact_text = re.sub(r"\\s+", " ", body_text).strip()[:50000]\n\n    nav = navigation or {}\n    page_status = classify_page_status(\n        nav, str(nav.get("target_url", page.url)), page.url\n    )\n'''
    text = replace_once(text, old_collection, new_collection, "safe page extraction")

    text = replace_once(
        text,
        '        "navigation": navigation or {},\n        "screenshot_error": screenshot_error,',
        '        "status": page_status,\n        "navigation": nav,\n        "extraction_errors": extraction_errors,\n        "screenshot_error": screenshot_error,',
        "evidence classification",
    )
    text = replace_once(
        text,
        '        "version": "0.2.0",',
        '        "version": "0.3.0",',
        "health version",
    )

    APP_PATH.write_text(text, encoding="utf-8")
    print("Applied AI-BIT browser worker build patch 0.3.0")


if __name__ == "__main__":
    main()
