from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "AI-BIT"
    bitrix_webhook_url: str = ""
    bitrix_verify_tls: bool = True
    bitrix_request_timeout: float = 30.0
    reports_dir: Path = Path("/app/reports")


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


async def bitrix_call(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.bitrix_webhook_url:
        raise HTTPException(status_code=503, detail="BITRIX_WEBHOOK_URL is not configured")

    url = f"{settings.bitrix_webhook_url.rstrip('/')}/{method}.json"
    try:
        async with httpx.AsyncClient(
            timeout=settings.bitrix_request_timeout,
            verify=settings.bitrix_verify_tls,
        ) as client:
            response = await client.post(url, json=params or {})
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Bitrix24 request failed: {exc}") from exc

    payload = response.json()
    if "error" in payload:
        raise HTTPException(
            status_code=502,
            detail=f"Bitrix24 API error: {payload['error']}: {payload.get('error_description', '')}",
        )
    return payload


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/v1/bitrix/status")
async def bitrix_status() -> dict[str, Any]:
    result = await bitrix_call("profile")
    return {"connected": True, "profile": result.get("result", {})}


@app.post("/api/v1/audits/run")
async def run_audit() -> dict[str, Any]:
    methods = {
        "profile": ("profile", {}),
        "users": ("user.get", {}),
        "departments": ("department.get", {}),
        "crm_statuses": ("crm.status.list", {}),
        "crm_deal_fields": ("crm.deal.fields", {}),
        "crm_contact_fields": ("crm.contact.fields", {}),
        "crm_company_fields": ("crm.company.fields", {}),
    }

    collected: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for key, (method, params) in methods.items():
        try:
            collected[key] = (await bitrix_call(method, params)).get("result")
        except HTTPException as exc:
            errors[key] = str(exc.detail)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.reports_dir / f"audit-{timestamp}.json"
    report_path.write_text(
        __import__("json").dumps(
            {"generated_at": timestamp, "data": collected, "errors": errors},
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    return {
        "status": "completed" if not errors else "completed_with_errors",
        "report": str(report_path),
        "sections_collected": list(collected),
        "errors": errors,
    }
