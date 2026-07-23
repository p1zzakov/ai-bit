from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIBIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI-BIT Enterprise"
    version: str = "7.0.0-alpha.1"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    storage_root: Path = Field(default=Path("/app/data"))
    plugin_paths: list[Path] = Field(default_factory=lambda: [Path("/app/plugins")])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
