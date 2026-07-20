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
        'app = FastAPI(title="AI-BIT Browser Worker", version="0.4.0")',
        "application version",
    )

    text = replace_once(
        text,
        '    wait_for: str | None = None',
        '    wait_for: str | list[str] | None = None',
        "scan request wait selectors",
    )

    old_presets = '''READ_ONLY_PRESETS: dict[str, str] = {
    "home": "/",
    "crm": "/crm/",
    "tasks": "/company/personal/user/0/tasks/",
    "groups": "/workgroups/",
    "disk": "/docs/",
    "knowledge": "/knowledge/",
    "calendar": "/calendar/",
    "company": "/company/",
    "contact_center": "/contact_center/",
    "openlines": "/services/openlines/",
    "bizproc": "/bizproc/",
    "rpa": "/rpa/",
    "market": "/marketplace/",
}
'''
    new_presets = '''PRESET_CONFIG_PATH = Path("/app/presets.json")


def load_preset_config() -> dict[str, dict[str, Any]]:
    if not PRESET_CONFIG_PATH.exists():
        raise RuntimeError(f"Preset configuration not found: {PRESET_CONFIG_PATH}")
    raw = json.loads(PRESET_CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("Preset configuration must be a JSON object")
    result: dict[str, dict[str, Any]] = {}
    for name, item in raw.items():
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise RuntimeError(f"Invalid preset configuration: {name}")
        wait_for = item.get("wait_for", [])
        if isinstance(wait_for, str):
            wait_for = [wait_for]
        result[str(name)] = {
            "path": item["path"],
            "wait_for": [str(selector) for selector in wait_for],
            "critical": bool(item.get("critical", False)),
        }
    return result


PRESET_CONFIG = load_preset_config()
READ_ONLY_PRESETS: dict[str, str] = {
    name: str(item["path"]) for name, item in PRESET_CONFIG.items()
}
'''
    text = replace_once(text, old_presets, new_presets, "configurable presets")

    text = replace_once(
        text,
        '    body_text = (await page.locator("body").inner_text()).lower()',
        '''    try:
        body_text = str(
            await page.evaluate(
                "() => document.body?.innerText || document.documentElement?.innerText || ''"
            )
        ).lower()
    except PlaywrightError:
        body_text = ""''',
        "non-blocking authentication text",
    )

    marker = "\n\nasync def collect_page(\n"
    helpers = '''

def classify_page_status(
    navigation: dict[str, Any],
    target_url: str,
    final_url: str,
    visible_text: str,
    title: str,
) -> str:
    http_status = navigation.get("http_status")
    if http_status in (401, 403):
        return "denied"
    if http_status == 404:
        return "not_found"
    if navigation.get("status") == "error":
        return "error"
    if not visible_text.strip() and not title.strip():
        return "partial"
    if navigation.get("timed_out"):
        return "partial"
    if final_url.rstrip("/") != target_url.rstrip("/"):
        return "redirected"
    return "ok"


async def safe_title(page: Page) -> tuple[str, str | None]:
    try:
        return await page.title(), None
    except PlaywrightError as exc:
        return "", str(exc)


async def safe_inner_texts(page: Page, selector: str) -> tuple[list[str], str | None]:
    try:
        values = await page.locator(selector).evaluate_all(
            "els => els.slice(0,100).map(el => (el.innerText || '').trim())"
        )
        return [str(value) for value in values], None
    except PlaywrightError as exc:
        return [], str(exc)


async def safe_links(page: Page) -> tuple[list[dict[str, str]], str | None]:
    try:
        links = await page.locator("a[href]").evaluate_all(
            "els => els.slice(0,500).map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text || x.href)"
        )
        return links, None
    except PlaywrightError as exc:
        return [], str(exc)


async def safe_body_text(page: Page) -> tuple[str, str | None]:
    try:
        value = await page.evaluate(
            "() => document.body?.innerText || document.documentElement?.innerText || ''"
        )
        return str(value), None
    except PlaywrightError as exc:
        return "", str(exc)


async def wait_for_any(page: Page, selectors: str | list[str] | None) -> dict[str, Any]:
    if not selectors:
        return {"matched": None, "attempted": [], "timed_out": False}
    candidates = [selectors] if isinstance(selectors, str) else selectors
    attempted: list[str] = []
    for selector in candidates:
        attempted.append(selector)
        try:
            await page.locator(selector).first.wait_for(state="attached", timeout=5000)
            return {"matched": selector, "attempted": attempted, "timed_out": False}
        except PlaywrightTimeoutError:
            continue
        except PlaywrightError as exc:
            return {
                "matched": None,
                "attempted": attempted,
                "timed_out": False,
                "error": str(exc),
            }
    return {"matched": None, "attempted": attempted, "timed_out": True}


def build_scan_summary(
    results: list[dict[str, Any]], errors: list[dict[str, str]]
) -> dict[str, Any]:
    counts = {key: 0 for key in ("ok", "redirected", "partial", "denied", "not_found", "error")}
    critical_findings: list[dict[str, str]] = []
    successful = 0
    for result in results:
        status = str(result.get("status", "error"))
        counts[status] = counts.get(status, 0) + 1
        if status in {"ok", "redirected"}:
            successful += 1
        preset = PRESET_CONFIG.get(str(result.get("name")), {})
        if preset.get("critical") and status not in {"ok", "redirected"}:
            critical_findings.append(
                {
                    "name": str(result.get("name")),
                    "status": status,
                    "url": str(result.get("url", "")),
                }
            )
    total = len(results) + len(errors)
    coverage = round(successful * 100 / total) if total else 0
    return {
        "total": total,
        "successful": successful,
        "coverage_percent": coverage,
        "status_counts": counts,
        "critical_findings": critical_findings,
        "runtime_errors": len(errors),
    }
'''
    if marker not in text:
        raise RuntimeError("collect_page marker not found")
    text = text.replace(marker, helpers + marker, 1)

    old_collection = '''    html_content = await page.content()
    html_path.write_text(html_content, encoding="utf-8")
    title = await page.title()
    headings = await page.locator("h1, h2, h3").all_inner_texts()
    menu_text = await page.locator(
        "nav, aside, [class*=menu], [class*=sidebar], [class*=navigation]"
    ).all_inner_texts()
    links = await page.locator("a[href]").evaluate_all(
        "els => els.slice(0,500).map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text || x.href)"
    )
    body_text = await page.locator("body").inner_text()
    compact_text = re.sub(r"\\s+", " ", body_text).strip()[:50000]
'''
    new_collection = '''    extraction_errors: dict[str, str] = {}
    try:
        html_content = await page.content()
    except PlaywrightError as exc:
        html_content = ""
        extraction_errors["html"] = str(exc)
    html_path.write_text(html_content, encoding="utf-8")

    title, error = await safe_title(page)
    if error:
        extraction_errors["title"] = error
    headings, error = await safe_inner_texts(page, "h1, h2, h3")
    if error:
        extraction_errors["headings"] = error
    menu_text, error = await safe_inner_texts(
        page, "nav, aside, [class*=menu], [class*=sidebar], [class*=navigation]"
    )
    if error:
        extraction_errors["menu_text"] = error
    links, error = await safe_links(page)
    if error:
        extraction_errors["links"] = error
    body_text, error = await safe_body_text(page)
    if error:
        extraction_errors["visible_text"] = error
    compact_text = re.sub(r"\\s+", " ", body_text).strip()[:50000]

    nav = navigation or {}
    page_status = classify_page_status(
        nav,
        str(nav.get("target_url", page.url)),
        page.url,
        compact_text,
        title,
    )
'''
    text = replace_once(text, old_collection, new_collection, "safe page extraction")

    text = replace_once(
        text,
        '        "navigation": navigation or {},\n        "screenshot_error": screenshot_error,',
        '        "status": page_status,\n        "navigation": nav,\n        "extraction_errors": extraction_errors,\n        "screenshot_error": screenshot_error,',
        "evidence classification",
    )

    old_wait = '''        if request.wait_for:
            try:
                await page.locator(request.wait_for).first.wait_for(
                    state="visible", timeout=15000
                )
            except PlaywrightTimeoutError as exc:
                navigation["wait_for_error"] = str(exc)
'''
    new_wait = '''        wait_result = await wait_for_any(page, request.wait_for)
        navigation["readiness"] = wait_result
        if wait_result.get("timed_out"):
            navigation["timed_out"] = True
'''
    text = replace_once(text, old_wait, new_wait, "configurable readiness wait")

    text = replace_once(
        text,
        '''@app.get("/presets")
async def presets() -> dict[str, str]:
    return READ_ONLY_PRESETS
''',
        '''@app.get("/presets")
async def presets() -> dict[str, dict[str, Any]]:
    return PRESET_CONFIG
''',
        "preset metadata endpoint",
    )

    text = replace_once(
        text,
        '''    return await scan_one(ScanRequest(name=preset, path=path))''',
        '''    preset_config = PRESET_CONFIG[preset]
    return await scan_one(
        ScanRequest(
            name=preset,
            path=path,
            wait_for=preset_config.get("wait_for", []),
        )
    )''',
        "preset readiness selectors",
    )

    old_batch_return = '''    return {
        "status": "completed" if not errors else "completed_with_errors",
        "results": results,
        "errors": errors,
    }
'''
    new_batch_return = '''    return {
        "status": "completed" if not errors else "completed_with_errors",
        "summary": build_scan_summary(results, errors),
        "results": results,
        "errors": errors,
    }
'''
    text = replace_once(text, old_batch_return, new_batch_return, "scan scorecard")

    text = replace_once(
        text,
        '''                ScanRequest(name=name, path=path)
                for name, path in READ_ONLY_PRESETS.items()''',
        '''                ScanRequest(
                    name=name,
                    path=path,
                    wait_for=PRESET_CONFIG[name].get("wait_for", []),
                )
                for name, path in READ_ONLY_PRESETS.items()''',
        "scan all preset readiness",
    )

    text = replace_once(
        text,
        '        "version": "0.2.0",',
        '        "version": "0.4.0",',
        "health version",
    )

    APP_PATH.write_text(text, encoding="utf-8")
    print("Applied AI-BIT browser worker build patch 0.4.0")


if __name__ == "__main__":
    main()
