from __future__ import annotations

import json
import os
from typing import Any

from groq import APIConnectionError, APIStatusError, Groq, RateLimitError


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
        "Ответ возвращай на русском языке в JSON с полями: "
        "summary, findings, actions, risks, expected_effect."
    )

    client = Groq(api_key=api_key, timeout=90.0)
    try:
        completion = client.chat.completions.create(
            model=status["model"],
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"question": question, "context": context},
                        ensure_ascii=False,
                    ),
                },
            ],
        )
    except RateLimitError as exc:
        raise RuntimeError("Groq API rate limit exceeded. Повторите запрос позже.") from exc
    except APIStatusError as exc:
        body = getattr(exc, "body", None)
        detail = json.dumps(body, ensure_ascii=False) if body else str(exc)
        raise RuntimeError(f"Groq API HTTP {exc.status_code}: {detail[:1500]}") from exc
    except APIConnectionError as exc:
        raise RuntimeError(f"Groq API connection failed: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Groq API unexpected error: {type(exc).__name__}: {exc}") from exc

    content = completion.choices[0].message.content or "{}"
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "summary": content,
            "findings": [],
            "actions": [],
            "risks": [],
            "expected_effect": "",
        }

    usage = completion.usage.model_dump() if completion.usage else {}
    return {
        "provider": status["provider"],
        "model": status["model"],
        "result": result,
        "usage": usage,
    }
