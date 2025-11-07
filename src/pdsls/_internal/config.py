"""configuration management for pdsls."""

from __future__ import annotations

import warnings
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# suppress pydantic warning about Field defaults
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._generate_schema")


class Settings(BaseSettings):
    """settings for atproto cli."""

    model_config = SettingsConfigDict(
        env_file=str(Path.cwd() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    atproto_pds_url: str = Field(default="https://bsky.social")
    atproto_handle: str = Field(default="")
    atproto_password: str = Field(default="")


settings = Settings()
