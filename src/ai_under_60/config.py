"""Configuration management for AI Under 60.

This module provides basic application configuration loaded from environment
variables and an optional .env file using Python standard library only.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Optional

# Valid standard log levels
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"



def _load_env_file(env_path: Optional[Path] = None) -> None:
    """Load key-value pairs from a .env file into os.environ if not already set.

    Standard-library alternative to python-dotenv for Milestone 0.1.
    """
    if env_path is None:
        # Default project root: 2 levels up from src/ai_under_60/
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"

    if not env_path.is_file():
        return

    try:
        with env_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    # Do not overwrite existing environment variables
                    if key and key not in os.environ:
                        os.environ[key] = val
    except OSError:
        # If reading .env fails, continue with existing environment variables
        pass


@dataclass(frozen=True)
class AppConfig:
    """Application configuration container."""

    app_env: str = "development"
    log_level: str = "INFO"
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    gemini_api_key: Optional[str] = field(default=None, repr=False)
    gemini_model: str = DEFAULT_GEMINI_MODEL

    @property
    def is_gemini_configured(self) -> bool:
        """Check whether a Gemini API key is configured."""
        return bool(self.gemini_api_key and self.gemini_api_key.strip())


def get_config(
    env_file: Optional[Path] = None,
    load_env: bool = True,
    project_root: Optional[Path] = None,
) -> AppConfig:
    """Load and return application configuration.

    Args:
        env_file: Optional path to a .env file to load.
        load_env: Whether to load environment variables from a .env file.
        project_root: Optional custom project root path.

    Returns:
        Configured AppConfig instance.
    """
    if load_env:
        _load_env_file(env_file)

    app_env = os.getenv("APP_ENV", "development").strip()
    if not app_env:
        app_env = "development"

    raw_log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    log_level = raw_log_level if raw_log_level in VALID_LOG_LEVELS else "INFO"

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
    raw_gemini_model = os.getenv("GEMINI_MODEL", "").strip()
    if not raw_gemini_model or raw_gemini_model == "gemini-2.5-flash":
        gemini_model = DEFAULT_GEMINI_MODEL
    else:
        gemini_model = raw_gemini_model


    root = project_root if project_root is not None else Path(__file__).resolve().parent.parent.parent

    return AppConfig(
        app_env=app_env,
        log_level=log_level,
        project_root=root,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )


