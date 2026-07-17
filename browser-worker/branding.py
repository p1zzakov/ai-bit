from __future__ import annotations

import hashlib
import json
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

PRODUCT_NAME = "AI-BIT Enterprise"
DEVELOPER_NAME = "Коваленко А.С."
DEVELOPER_EMAIL = "pizzakov@gmail.com"
COPYRIGHT_YEAR = "2026"
BRAND_MARKER = "ai-bit-developer-attribution"
_EXPECTED_DIGEST = "024b9f5536e9a70f7e72f2885b55d09766ee6cc9b9a39463b901725b2f682882"


def _canonical_payload() -> dict[str, str]:
    return {
        "product": PRODUCT_NAME,
        "developer": DEVELOPER_NAME,
        "contact": DEVELOPER_EMAIL,
        "year": COPYRIGHT_YEAR,
        "marker": BRAND_MARKER,
    }


def _digest() -> str:
    raw = json.dumps(_canonical_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def product_metadata(version: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = _canonical_payload()
    if version:
        result["version"] = version
    result["brand_integrity"] = brand_integrity()
    return result


def brand_integrity() -> dict[str, Any]:
    actual = _digest()
    ok = actual == _EXPECTED_DIGEST
    return {
        "status": "ok" if ok else "warning",
        "valid": ok,
        "marker": BRAND_MARKER,
        "message": (
            "Developer attribution configuration is intact"
            if ok
            else "Developer attribution configuration was changed"
        ),
    }


def attribution_fragment() -> str:
    return f'''<style id="{BRAND_MARKER}-style">
#{BRAND_MARKER}{{position:fixed;right:16px;bottom:12px;z-index:2147483000;padding:7px 11px;border:1px solid rgba(148,163,184,.25);border-radius:10px;background:rgba(8,15,28,.88);backdrop-filter:blur(12px);box-shadow:0 8px 28px rgba(0,0,0,.28);font:11px/1.35 Inter,Segoe UI,Arial,sans-serif;color:#9fb0c8;letter-spacing:.1px;user-select:text}}
#{BRAND_MARKER} b{{color:#eef5ff;font-weight:650}}#{BRAND_MARKER} a{{color:#8cabff;text-decoration:none}}#{BRAND_MARKER} a:hover{{text-decoration:underline}}
@media print{{#{BRAND_MARKER}{{position:fixed;right:8mm;bottom:5mm;background:#fff;color:#667085;border-color:#d0d5dd;box-shadow:none}}#{BRAND_MARKER} b{{color:#101828}}}}
</style><div id="{BRAND_MARKER}" data-brand-integrity="{_digest()}">Разработчик: <b>{DEVELOPER_NAME}</b> · <a href="mailto:{DEVELOPER_EMAIL}">{DEVELOPER_EMAIL}</a></div>'''


def inject_attribution(html: str) -> str:
    if BRAND_MARKER in html:
        return html
    fragment = attribution_fragment()
    pos = html.lower().rfind("</body>")
    if pos >= 0:
        return html[:pos] + fragment + html[pos:]
    return html + fragment


class BrandingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            return response
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        charset = getattr(response, "charset", None) or "utf-8"
        html = body.decode(charset, errors="replace")
        branded = inject_attribution(html).encode(charset)
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=branded,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type or "text/html",
            background=response.background,
        )


def install_branding(app: Any) -> None:
    app.add_middleware(BrandingMiddleware)


def about_page_html(version: str) -> str:
    integrity = brand_integrity()
    status = "Целостность подтверждена" if integrity["valid"] else "Обнаружено изменение конфигурации"
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>О системе — {PRODUCT_NAME}</title><style>
:root{{color-scheme:dark;--bg:#07101d;--panel:#101b2d;--line:#283956;--text:#eef5ff;--muted:#91a3bd;--accent:#6d8cff;--ok:#35d08a;--warn:#fbbf24}}*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;font:14px/1.55 Inter,Segoe UI,Arial,sans-serif;background:radial-gradient(circle at 75% 10%,rgba(109,140,255,.14),transparent 30%),var(--bg);color:var(--text)}}main{{max-width:900px;margin:auto;padding:48px 24px 100px}}.hero{{padding:30px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(145deg,rgba(20,32,54,.96),rgba(11,19,33,.96));box-shadow:0 24px 70px rgba(0,0,0,.28)}}.logo{{width:64px;height:64px;border-radius:18px;display:grid;place-items:center;font-weight:900;font-size:22px;background:linear-gradient(135deg,#6d8cff,#8b5cf6);box-shadow:0 14px 36px rgba(109,140,255,.28)}}h1{{font-size:34px;margin:22px 0 6px}}h2{{margin-top:28px}}.muted{{color:var(--muted)}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:24px}}.card{{padding:18px;border:1px solid var(--line);border-radius:15px;background:rgba(16,27,45,.86)}}.label{{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted)}}.value{{font-size:18px;margin-top:6px}}a{{color:#8cabff}}.integrity{{margin-top:22px;padding:15px;border-radius:13px;border:1px solid {'rgba(53,208,138,.35)' if integrity['valid'] else 'rgba(251,191,36,.35)'};background:{'rgba(53,208,138,.08)' if integrity['valid'] else 'rgba(251,191,36,.08)'}}}@media(max-width:650px){{.grid{{grid-template-columns:1fr}}h1{{font-size:27px}}}}
</style></head><body><main><section class="hero"><div class="logo">AI</div><h1>{PRODUCT_NAME}</h1><div class="muted">Платформа непрерывного интеллектуального аудита и управленческой аналитики Bitrix24.</div><div class="grid"><div class="card"><div class="label">Версия</div><div class="value">{version}</div></div><div class="card"><div class="label">Режим</div><div class="value">Read-only audit</div></div><div class="card"><div class="label">Разработчик</div><div class="value">{DEVELOPER_NAME}</div></div><div class="card"><div class="label">Контакт</div><div class="value"><a href="mailto:{DEVELOPER_EMAIL}">{DEVELOPER_EMAIL}</a></div></div></div><div class="integrity"><b>Brand Integrity:</b> {status}</div><h2>Принципы</h2><p class="muted">Фактические evidence, воспроизводимые оценки, прозрачные рекомендации и отсутствие скрытого воздействия на исходный портал.</p></section></main></body></html>'''
