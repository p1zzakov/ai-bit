from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from playwright.async_api import async_playwright


BASE_URL = os.environ["BROWSER_BASE_URL"].rstrip("/") + "/"
LOGIN_PATH = os.environ.get("BROWSER_LOGIN_PATH", "/auth/").lstrip("/")
LOGIN = os.environ["BROWSER_LOGIN"]
PASSWORD = os.environ["BROWSER_PASSWORD"]
IGNORE_HTTPS_ERRORS = os.environ.get("BROWSER_IGNORE_HTTPS_ERRORS", "false").lower() == "true"
HEADLESS = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"
TIMEOUT_MS = int(os.environ.get("BROWSER_TIMEOUT_MS", "45000"))
ARTIFACTS_ROOT = Path(os.environ.get("BROWSER_ARTIFACTS_DIR", "/app/artifacts"))


def compact(text: str, limit: int = 12000) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


async def main() -> None:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = ARTIFACTS_ROOT / stamp / "login-debug"
    out.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            ignore_https_errors=IGNORE_HTTPS_ERRORS,
            viewport={"width": 1600, "height": 1000},
            locale="ru-RU",
        )
        context.set_default_timeout(TIMEOUT_MS)
        page = await context.new_page()

        target = urljoin(BASE_URL, LOGIN_PATH)
        await page.goto(target, wait_until="domcontentloaded")

        login_input = page.locator(
            'input[name="USER_LOGIN"], input[name="login"], input[type="email"]'
        ).first
        password_input = page.locator(
            'input[name="USER_PASSWORD"], input[name="password"], input[type="password"]'
        ).first

        if await login_input.count() == 0 or await password_input.count() == 0:
            raise RuntimeError("Login form was not recognized")

        await login_input.fill(LOGIN)
        await password_input.fill(PASSWORD)

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

        body_text = await page.locator("body").inner_text()
        inputs = await page.locator("input").evaluate_all(
            """els => els.map(e => ({
                name: e.name,
                type: e.type,
                id: e.id,
                placeholder: e.placeholder,
                visible: !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
            }))"""
        )
        buttons = await page.locator("button, input[type=submit]").evaluate_all(
            """els => els.slice(0,100).map(e => ({
                text: (e.innerText || e.value || '').trim(),
                type: e.type || '',
                visible: !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
            }))"""
        )

        await page.screenshot(path=str(out / "after-login.png"), full_page=True)
        (out / "after-login.html").write_text(await page.content(), encoding="utf-8")
        (out / "after-login.txt").write_text(body_text, encoding="utf-8")

        result = {
            "generated_at": datetime.now(UTC).isoformat(),
            "url": page.url,
            "title": await page.title(),
            "visible_text": compact(body_text),
            "inputs": inputs,
            "buttons": buttons,
            "artifacts": {
                "screenshot": str(out / "after-login.png"),
                "html": str(out / "after-login.html"),
                "text": str(out / "after-login.txt"),
            },
        }
        (out / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
