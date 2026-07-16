from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def ai_status() -> dict[str, Any]:
    provider = os.getenv("AI_PROVIDER", "groq").strip().lower()
    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile").strip()
    configured = bool(os.getenv("GROQ_API_KEY")) if provider == "groq" else False
    return {"provider": provider, "model": model, "configured": configured}


def generate_advice(context: dict[str, Any], question: str) -> dict[str, Any]:
    status = ai_status()
    if status["provider"] != "groq":
        raise RuntimeError(f"Unsupported AI provider: {status['provider']}")
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    system = (
        "Ты корпоративный консультант по внедрению Bitrix24. "
        "Работай только по переданным фактам, не выдумывай данные. "
        "Ответ возвращай на русском языке в JSON с полями: summary, findings, actions, risks, expected_effect."
    )
    payload = {
        "model": status["model"],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps({"question": question, "context": context}, ensure_ascii=False)},
        ],
    }
    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Groq API HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:1000]}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Groq API connection failed: {exc}") from exc

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"summary": content, "findings": [], "actions": [], "risks": [], "expected_effect": ""}
    return {"provider": status["provider"], "model": status["model"], "result": result, "usage": data.get("usage", {})}
