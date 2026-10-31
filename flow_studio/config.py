"""FLOW Studio: Strongly-Typed Environment & Server Settings.

Separates configuration state from application logic.
Supports environment overrides (FLOW_HOST, FLOW_PORT, FLOW_DEBUG, etc.).
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from flow_studio.constants import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DEFAULT_TEMPERATURE,
    MAX_TOKEN_LIMIT,
    MIN_TOKEN_LIMIT,
)

PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent
WORKSPACE_ROOT: Final[Path] = PACKAGE_ROOT.parent


@dataclass(frozen=True)
class AppSettings:
    """Immutable application configuration."""

    app_name: str = "FLOW Studio (by Project Pyrite)"
    version: str = "1.0.0"
    host: str = os.getenv("FLOW_HOST", DEFAULT_SERVER_HOST)
    port: int = int(os.getenv("FLOW_PORT", str(DEFAULT_SERVER_PORT)))
    debug: bool = os.getenv("FLOW_DEBUG", "false").lower() in ("true", "1")
    default_max_tokens: int = int(os.getenv("FLOW_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
    min_token_limit: int = MIN_TOKEN_LIMIT
    max_token_limit: int = MAX_TOKEN_LIMIT
    default_temperature: float = DEFAULT_TEMPERATURE

    # Directory Paths
    package_dir: Path = PACKAGE_ROOT
    static_dir: Path = PACKAGE_ROOT / "static"
    workspace_dir: Path = WORKSPACE_ROOT

    # DeepSeek Local Model Path if present
    deepseek_model_path: Path = (
        WORKSPACE_ROOT
        / "pyrite-mlx"
        / "results"
        / "models"
        / "deepseek_coder_v2_lite_pyrite_final_mlx"
    )

    # Mixtral Local Model Path if present
    mixtral_model_path: Path = (
        Path("/Volumes/NVMe2TB/AI-LLM/models/Mixtral-8x22B-Instruct-v0.1-4bit")
    )


# Singleton settings instance
settings = AppSettings()

