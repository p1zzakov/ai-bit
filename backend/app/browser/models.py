from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BrowserEvidence(BaseModel):
    generated_at: str
    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    url: str
    title: str = ""
    headings: list[str] = Field(default_factory=list)
    menu_text: list[str] = Field(default_factory=list)
    links: list[dict[str, Any]] = Field(default_factory=list)
    visible_text: str = ""
    navigation: dict[str, Any] = Field(default_factory=dict)
    screenshot_error: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    source: str = "browser-worker"


class BrowserEvidenceReceipt(BaseModel):
    status: str
    evidence_id: str
    name: str
    generated_at: str
