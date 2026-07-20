from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from fastapi import FastAPI, HTTPException
from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    browser_base_url: str = ""
    browser_login: str = ""
    browser_password: str = ""
    browser_login_path: str = "/auth/"
    browser_headless: bool = True
    browser_ignore_https_errors: bool = False
    browser_timeout_ms: int = 45000
    browser_artifacts_dir: Path = Path("/app/artifacts")
    browser_state_file: Path = Path("/app/state/bitrix-storage-state.json")


settings = Settings()
app = FastAPI(title="AI-BIT Browser Worker", version="0.2.0")
PLAYWRIGHT = None
BROWSER: Browser | None = None


class ScanRequest(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    path: str
    wait_for: str | None = None
    full_page: bool = True


class BatchScanRequest(BaseModel):
    pages: list[ScanRequest]


READ_ONLY_PRESETS: dict[str, str] = {
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


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def ensure_configured() -> None:
    if not settings.browser_base_url:
        raise HTTPException(status_code=503, detail="BROWSER_BASE_URL is not configured")


def same_origin(url: str) -> bool:
    base = urlparse(settings.browser_base_url)
    target = urlparse(url)
    return (base.scheme, base.netloc) == (target.scheme, target.netloc)


async def new_context() -> BrowserContext:
    if BROWSER is None:
        raise HTTPException(status_code=503, detail="Browser is not started")
    kwargs: dict[str, Any] = {
        "ignore_https_errors": settings.browser_ignore_https_errors,
        "viewport": {"width": 1600, "height": 1000},
        "locale": "ru-RU",
    }
    if settings.browser_state_file.exists():
        kwargs["storage_state"] = str(settings.browser_state_file)
    context = await BROWSER.new_context(**kwargs)
    context.set_default_timeout(settings.browser_timeout_ms)
    return context


async def is_authenticated(page: Page) -> bool:
    """Detect an authenticated Bitrix24 session without relying on the URL."""
    logout = page.locator(
        'a[href*="logout"], '
        'a:has-text("Выйти"), '
        'button:has-text("Выйти"), '
        'a:has-text("Log out"), '
        'button:has-text("Log out")'
    )
    if await logout.count() > 0:
        return True

    body_text = (await page.locator("body").inner_text()).lower()
    success_markers = (
        "успешно авторизовались",
        "вы зарегистрированы и успешно авторизовались",
        "successfully authorized",
        "successfully logged in",
    )
    if any(marker in body_text for marker in success_markers):
        return True

    login_input = page.locator(
        'input[name="USER_LOGIN"], input[name="login"], input[type="email"]'
    ).first
    password_input = page.locator(
        'input[name="USER_PASSWORD"], input[name="password"], input[type="password"]'
    ).first

    login_visible = await login_input.count() > 0 and await login_input.is_visible()
    password_visible = await password_input.count() > 0 and await password_input.is_visible()
    return not login_visible and not password_visible


async def navigate_page(page: Page, target: str) -> dict[str, Any]:
    """Navigate without losing evidence when Bitrix keeps the request open.

    Some Bitrix pages do not complete ``domcontentloaded`` within the global
    timeout because of redirects, long-running PHP requests or frontend
    bootstrap behaviour. A timeout is therefore recorded as evidence rather
    than propagated as an HTTP 500 response.
    """
    diagnostics: dict[str, Any] = {
        "target_url": target,
        "final_url": page.url,
        "status": "pending",
        "http_status": None,
        "timed_out": False,
        "error": None,
        "console": [],
        "page_errors": [],
        "request_failures": [],
        "http_errors": [],
    }

    page.on(
        "console",
        lambda message: diagnostics["console"].append(
            {"type": message.type, "text": message.text[:2000]}
        ),
    )
    page.on(
        "pageerror",
        lambda error: diagnostics["page_errors"].append(str(error)[:4000]),
    )
    page.on(
        "requestfailed",
        lambda request: diagnostics["request_failures"].append(
            {
                "url": request.url,
                "method": request.method,
                "failure": request.failure,
            }
        ),
    )

    def record_http_error(response: Any) -> None:
        if response.status >= 400:
            diagnostics["http_errors"].append(
                {"status": response.status, "url": response.url}
            )

    page.on("response", record_http_error)

    navigation_timeout_ms = min(settings.browser_timeout_ms, 20000)
    try:
        response = await page.goto(
            target,
            wait_until="commit",
            timeout=navigation_timeout_ms,
        )
        diagnostics["http_status"] = response.status if response else None
        diagnostics["status"] = "committed"
    except PlaywrightTimeoutError as exc:
        diagnostics["status"] = "timeout"
        diagnostics["timed_out"] = True
        diagnostics["error"] = str(exc)
    except PlaywrightError as exc:
        diagnostics["status"] = "error"
        diagnostics["error"] = str(exc)

    # Give Bitrix frontend time to render, but do not require a permanently idle network.
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
    except PlaywrightTimeoutError:
        diagnostics["timed_out"] = True

    await page.wait_for_timeout(3000)
    diagnostics["final_url"] = page.url
    diagnostics["console"] = diagnostics["console"][-100:]
    diagnostics["page_errors"] = diagnostics["page_errors"][-100:]
    diagnostics["request_failures"] = diagnostics["request_failures"][-100:]
    diagnostics["http_errors"] = diagnostics["http_errors"][-100:]
    return diagnostics


async def login(force: bool = False) -> dict[str, Any]:
    ensure_configured()
    if not settings.browser_login or not settings.browser_password:
        raise HTTPException(status_code=503, detail="Browser credentials are not configured")
    if force and settings.browser_state_file.exists():
        settings.browser_state_file.unlink()

    context = await new_context()
    page = await context.new_page()
    try:
        target = urljoin(
            settings.browser_base_url.rstrip("/") + "/",
            settings.browser_login_path.lstrip("/"),
        )
        await page.goto(target, wait_until="domcontentloaded")
        if await is_authenticated(page):
            await context.storage_state(path=str(settings.browser_state_file))
            return {"authenticated": True, "url": page.url, "reused_session": True}

        login_input = page.locator(
            'input[name="USER_LOGIN"], input[name="login"], input[type="email"]'
        ).first
        password_input = page.locator(
            'input[name="USER_PASSWORD"], input[name="password"], input[type="password"]'
        ).first
        if await login_input.count() == 0 or await password_input.count() == 0:
            raise HTTPException(
                status_code=422,
                detail="Login form was not recognized. Interactive/SSO login may be enabled.",
            )

        await login_input.fill(settings.browser_login)
        await password_input.fill(settings.browser_password)
        submit = page.locator(
            'button[type="submit"], input[type="submit"], '
            'button:has-text("Войти"), button:has-text("Log in")'
        ).first
        if await submit.count() == 0:
            await password_input.press("Enter")
        else:
            await submit.click()
        await page.wait_for_load_state("domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        if not await is_authenticated(page):
            raise HTTPException(status_code=401, detail="Bitrix24 browser authentication failed")

        settings.browser_state_file.parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(settings.browser_state_file))
        return {"authenticated": True, "url": page.url, "reused_session": False}
    finally:
        await context.close()


async def collect_page(
    page: Page,
    name: str,
    full_page: bool,
    navigation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stamp = utc_stamp()
    target_dir = settings.browser_artifacts_dir / stamp / name
    target_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = target_dir / "page.png"
    html_path = target_dir / "page.html"
    evidence_path = target_dir / "evidence.json"

    screenshot_error: str | None = None
    try:
        await page.screenshot(path=str(screenshot_path), full_page=full_page, timeout=30000)
    except PlaywrightError as exc:
        screenshot_error = str(exc)

    html_content = await page.content()
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
    compact_text = re.sub(r"\s+", " ", body_text).strip()[:50000]

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "name": name,
        "url": page.url,
        "title": title,
        "headings": headings[:100],
        "menu_text": menu_text[:100],
        "links": links,
        "visible_text": compact_text,
        "navigation": navigation or {},
        "screenshot_error": screenshot_error,
        "artifacts": {
            "screenshot": str(screenshot_path) if screenshot_error is None else None,
            "html": str(html_path),
            "evidence": str(evidence_path),
        },
    }
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return evidence


async def scan_one(request: ScanRequest) -> dict[str, Any]:
    ensure_configured()
    context = await new_context()
    try:
        page = await context.new_page()
        target = urljoin(
            settings.browser_base_url.rstrip("/") + "/", request.path.lstrip("/")
        )
        if not same_origin(target):
            raise HTTPException(
                status_code=400,
                detail="Only the configured Bitrix24 origin is allowed",
            )

        navigation = await navigate_page(page, target)
        if not await is_authenticated(page):
            await context.close()
            await login()
            context = await new_context()
            page = await context.new_page()
            navigation = await navigate_page(page, target)

        if not await is_authenticated(page):
            raise HTTPException(status_code=401, detail="Bitrix24 browser authentication failed")

        if request.wait_for:
            try:
                await page.locator(request.wait_for).first.wait_for(
                    state="visible", timeout=15000
                )
            except PlaywrightTimeoutError as exc:
                navigation["wait_for_error"] = str(exc)

        return await collect_page(
            page,
            request.name,
            request.full_page,
            navigation=navigation,
        )
    finally:
        await context.close()


@app.on_event("startup")
async def startup() -> None:
    global PLAYWRIGHT, BROWSER
    settings.browser_artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.browser_state_file.parent.mkdir(parents=True, exist_ok=True)
    PLAYWRIGHT = await async_playwright().start()
    BROWSER = await PLAYWRIGHT.chromium.launch(headless=settings.browser_headless)


@app.on_event("shutdown")
async def shutdown() -> None:
    if BROWSER is not None:
        await BROWSER.close()
    if PLAYWRIGHT is not None:
        await PLAYWRIGHT.stop()


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "AI-BIT Browser Worker",
        "version": "0.2.0",
        "configured": bool(settings.browser_base_url),
        "session_saved": settings.browser_state_file.exists(),
    }


@app.get("/presets")
async def presets() -> dict[str, str]:
    return READ_ONLY_PRESETS


@app.post("/login")
async def browser_login(force: bool = False) -> dict[str, Any]:
    return await login(force=force)


@app.post("/scan")
async def scan(request: ScanRequest) -> dict[str, Any]:
    return await scan_one(request)


@app.post("/scan/preset/{preset}")
async def scan_preset(preset: str) -> dict[str, Any]:
    path = READ_ONLY_PRESETS.get(preset)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Unknown preset: {preset}")
    return await scan_one(ScanRequest(name=preset, path=path))


@app.post("/scan/batch")
async def scan_batch(request: BatchScanRequest) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for item in request.pages:
        try:
            results.append(await scan_one(item))
        except HTTPException as exc:
            errors.append({"name": item.name, "error": str(exc.detail)})
        except Exception as exc:
            errors.append(
                {
                    "name": item.name,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return {
        "status": "completed" if not errors else "completed_with_errors",
        "results": results,
        "errors": errors,
    }


@app.post("/scan/all")
async def scan_all() -> dict[str, Any]:
    return await scan_batch(
        BatchScanRequest(
            pages=[
                ScanRequest(name=name, path=path)
                for name, path in READ_ONLY_PRESETS.items()
            ]
        )
    )
