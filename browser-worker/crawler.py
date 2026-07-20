from __future__ import annotations

import json
import re
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from playwright.async_api import BrowserContext, Page, Error as PlaywrightError
from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    start_path: str = "/"
    max_pages: int = Field(default=50, ge=1, le=500)
    max_depth: int = Field(default=2, ge=0, le=8)
    include_query: bool = False
    save_html: bool = False
    delay_ms: int = Field(default=250, ge=0, le=5000)


DEFAULT_SKIP_PATHS = (
    "/auth/",
    "/bitrix/admin/",
    "/bitrix/tools/",
    "/bitrix/services/",
    "/rest/",
    "/upload/",
)

DEFAULT_SKIP_FRAGMENTS = (
    "logout=yes",
    "action=download",
    "download=",
    "ajax=",
    "sessid=",
    "bxajaxid=",
)

# Bitrix24 is heavily SPA-driven: many menu items are not exposed as ordinary
# href links on the landing page. Seed the crawler with known read-only entry
# points so a crawl from "/" does not incorrectly stop after one page.
DEFAULT_SEED_PATHS = (
    "/crm/",
    "/company/personal/user/0/tasks/",
    "/company/",
    "/workgroups/",
    "/docs/",
    "/knowledge/",
    "/calendar/",
    "/bizproc/",
    "/rpa/",
    "/marketplace/",
    "/contact_center/",
    "/services/openlines/",
)

STATIC_EXTENSIONS = {
    ".css", ".js", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".doc", ".docx", ".xls",
    ".xlsx", ".zip", ".rar", ".7z", ".mp3", ".mp4", ".avi", ".mov",
}


ContextFactory = Callable[[], Awaitable[BrowserContext]]
LoginCallable = Callable[..., Awaitable[dict[str, Any]]]
AuthCallable = Callable[[Page], Awaitable[bool]]
NavigateCallable = Callable[[Page, str], Awaitable[dict[str, Any]]]


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def normalize_url(url: str, base_url: str, include_query: bool) -> str | None:
    absolute = urljoin(base_url.rstrip("/") + "/", url)
    parsed = urlparse(absolute)
    base = urlparse(base_url)
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    suffix = Path(path).suffix.lower()
    if suffix in STATIC_EXTENSIONS:
        return None
    lowered = absolute.lower()
    if any(fragment in lowered for fragment in DEFAULT_SKIP_FRAGMENTS):
        return None
    if any(path.startswith(prefix) for prefix in DEFAULT_SKIP_PATHS):
        return None
    query = ""
    if include_query and parsed.query:
        safe_pairs = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in {"sessid", "logout", "bxajaxid", "action"}
        ]
        query = urlencode(sorted(safe_pairs))
    return urlunparse((parsed.scheme, parsed.netloc, path, "", query, ""))


def section_for_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "home"
    first = path.split("/", 1)[0].lower()
    aliases = {
        "stream": "home",
        "crm": "crm",
        "company": "company",
        "workgroups": "groups",
        "docs": "disk",
        "knowledge": "knowledge",
        "calendar": "calendar",
        "services": "services",
        "bizproc": "page",
        "rpa": "rpa",
        "market": "market",
        "marketplace": "market",
        "contact_center": "contact_center",
    }
    # Tasks live below /company/personal/.../tasks/, so classify them before
    # falling back to the first URL segment.
    if "/tasks/" in f"/{path}/":
        return "tasks"
    if first == "services" and "/openlines/" in f"/{path}/":
        return "openlines"
    return aliases.get(first, first or "other")


async def extract_page(page: Page) -> dict[str, Any]:
    try:
        title = await page.title()
    except PlaywrightError:
        title = ""
    try:
        text = str(
            await page.evaluate(
                "() => document.body?.innerText || document.documentElement?.innerText || ''"
            )
        )
    except PlaywrightError:
        text = ""
    try:
        links = await page.locator("a[href]").evaluate_all(
            "els => els.slice(0,1500).map(a => ({text:(a.innerText||'').trim(), href:a.href}))"
        )
    except PlaywrightError:
        links = []
    return {
        "title": title,
        "visible_text": re.sub(r"\s+", " ", text).strip()[:2000],
        "links": links,
    }


async def crawl_portal(
    request: CrawlRequest,
    *,
    base_url: str,
    artifacts_dir: Path,
    new_context: ContextFactory,
    is_authenticated: AuthCallable,
    login: LoginCallable,
    navigate_page: NavigateCallable,
) -> dict[str, Any]:
    start_url = normalize_url(request.start_path, base_url, request.include_query)
    if start_url is None:
        raise ValueError("start_path must resolve to the configured Bitrix24 origin")

    stamp = utc_stamp()
    target_dir = artifacts_dir / stamp / "crawl"
    target_dir.mkdir(parents=True, exist_ok=True)
    map_path = target_dir / "site-map.json"

    queue: deque[tuple[str, int, str | None]] = deque([(start_url, 0, None)])
    scheduled = {start_url}

    # Seed known sections at depth 1. They remain subject to max_pages and all
    # normal read-only navigation/status checks.
    if request.max_depth > 0:
        for seed_path in DEFAULT_SEED_PATHS:
            seed_url = normalize_url(seed_path, base_url, request.include_query)
            if seed_url is None or seed_url in scheduled:
                continue
            scheduled.add(seed_url)
            queue.append((seed_url, 1, start_url))

    visited: set[str] = set()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    context = await new_context()
    page = await context.new_page()
    try:
        while queue and len(nodes) < request.max_pages:
            url, depth, parent = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            navigation = await navigate_page(page, url)
            if not await is_authenticated(page):
                await context.close()
                await login()
                context = await new_context()
                page = await context.new_page()
                navigation = await navigate_page(page, url)

            page_data = await extract_page(page)
            final_url = normalize_url(page.url, base_url, request.include_query) or page.url
            http_status = navigation.get("http_status")
            status = "ok"
            if http_status in {401, 403}:
                status = "denied"
            elif http_status == 404:
                status = "not_found"
            elif navigation.get("status") == "error":
                status = "error"
            elif navigation.get("timed_out"):
                status = "partial"
            elif final_url.rstrip("/") != url.rstrip("/"):
                status = "redirected"

            node: dict[str, Any] = {
                "url": final_url,
                "requested_url": url,
                "parent": parent,
                "depth": depth,
                "section": section_for_url(final_url),
                "title": page_data["title"],
                "status": status,
                "http_status": http_status,
                "navigation": navigation,
                "link_count": len(page_data["links"]),
                "text_sample": page_data["visible_text"],
            }

            if request.save_html:
                html_path = target_dir / f"page-{len(nodes)+1:04d}.html"
                try:
                    html_path.write_text(await page.content(), encoding="utf-8")
                    node["html"] = str(html_path)
                except PlaywrightError as exc:
                    node["html_error"] = str(exc)

            nodes.append(node)

            if parent:
                edges.append({"from": parent, "to": final_url})

            if depth < request.max_depth and status not in {"denied", "not_found", "error"}:
                for link in page_data["links"]:
                    normalized = normalize_url(
                        str(link.get("href", "")), base_url, request.include_query
                    )
                    if normalized is None or normalized in scheduled:
                        continue
                    scheduled.add(normalized)
                    queue.append((normalized, depth + 1, final_url))

            if request.delay_ms:
                await page.wait_for_timeout(request.delay_ms)
    except Exception as exc:
        errors.append({"url": page.url, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        await context.close()

    section_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for node in nodes:
        section = str(node["section"])
        status = str(node["status"])
        section_counts[section] = section_counts.get(section, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "start_url": start_url,
        "limits": {
            "max_pages": request.max_pages,
            "max_depth": request.max_depth,
            "include_query": request.include_query,
        },
        "summary": {
            "visited": len(nodes),
            "scheduled": len(scheduled),
            "remaining_queue": len(queue),
            "sections": section_counts,
            "statuses": status_counts,
            "errors": len(errors),
        },
        "nodes": nodes,
        "edges": edges,
        "errors": errors,
        "artifact": str(map_path),
    }
    map_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path = artifacts_dir / "latest-crawl.json"
    latest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
