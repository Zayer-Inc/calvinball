"""Pydantic Settings for Calvinball configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CALVINBALL_DIR = Path.home() / ".calvinball"
CONFIG_PATH = CALVINBALL_DIR / "config.toml"
DB_PATH = CALVINBALL_DIR / "calvinball.db"
GENERATED_TOOLS_DIR = CALVINBALL_DIR / "generated_tools"


class LLMSettings(BaseModel):
    model: str = "openai/gpt-4o"
    temperature: float = 0.2
    max_tokens: int = 4096
    max_iterations: int = 50


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CALVINBALL_",
        env_nested_delimiter="__",
    )

    llm: LLMSettings = Field(default_factory=LLMSettings)
    db_path: Path = DB_PATH
    output_dir: Path = CALVINBALL_DIR / "output"
    generated_tools_dir: Path = GENERATED_TOOLS_DIR

    @classmethod
    def load(cls) -> Settings:
        """Load settings from config file, env vars, and defaults."""
        overrides: dict[str, Any] = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "rb") as f:
                overrides = tomllib.load(f)
        return cls(**overrides)


def ensure_dirs() -> None:
    """Create the ~/.calvinball directory structure."""
    CALVINBALL_DIR.mkdir(exist_ok=True)
    (CALVINBALL_DIR / "output").mkdir(exist_ok=True)
    GENERATED_TOOLS_DIR.mkdir(exist_ok=True)


DEFAULT_CONFIG_TOML = """\
[llm]
model = "openai/gpt-4o"
temperature = 0.2
max_tokens = 4096
max_iterations = 50
"""
