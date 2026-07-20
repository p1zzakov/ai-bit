from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app import main as core
from app.implementation import router as implementation_router


BLOCKED_METHOD_TOKENS = {
    "add",
    "create",
    "update",
    "delete",
    "remove",
    "set",
    "import",
    "install",
    "uninstall",
    "execute",
    "start",
    "stop",
    "terminate",
    "pause",
    "resume",
    "send",
    "bind",
    "unbind",
    "register",
    "unregister",
}

_original_bitrix_call = core.bitrix_call


def _assert_read_only(method: str) -> None:
    normalized = method.strip().lower()
    tokens = {token for token in normalized.replace("_", ".").split(".") if token}
    blocked = sorted(tokens & BLOCKED_METHOD_TOKENS)
    if blocked:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Unsafe Bitrix24 REST method blocked: {method}. "
                "AI-BIT operates in strict READ-ONLY mode."
            ),
        )


async def guarded_bitrix_call(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    _assert_read_only(method)
    return await _original_bitrix_call(method, params)


core.bitrix_call = guarded_bitrix_call
core.app.include_router(implementation_router)
app = core.app
