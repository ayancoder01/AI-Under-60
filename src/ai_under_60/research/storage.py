"""Storage layer for saving and retrieving ResearchPackage artifacts."""

from datetime import datetime
from pathlib import Path
import re
from typing import Optional

from ai_under_60.config import get_config
from ai_under_60.logger import setup_logger
from ai_under_60.research.models import ResearchPackage

logger = setup_logger("ai_under_60.research.storage")


class ResearchStorageError(Exception):
    """Raised when saving or loading a ResearchPackage fails."""


def _slugify(text: str, max_length: int = 40, default: str = "research") -> str:
    """Convert a topic string into a clean, filesystem-safe filename slug."""
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    return slug[:max_length].strip("_") or default


def get_default_research_storage_dir() -> Path:
    """Get the default runtime directory for storing research packages."""
    config = get_config()
    return config.project_root / "data" / "research"


def save_research_package(
    package: ResearchPackage,
    storage_dir: Optional[Path] = None,
) -> Path:
    """Save a ResearchPackage instance to a JSON file.

    Args:
        package: Validated ResearchPackage instance.
        storage_dir: Optional custom target directory. Defaults to data/research.

    Returns:
        Path to the saved JSON file.

    Raises:
        ResearchStorageError: If the input is invalid or writing fails.
    """
    if not isinstance(package, ResearchPackage):
        raise ResearchStorageError(
            f"Expected ResearchPackage instance, got {type(package).__name__}."
        )

    target_dir = storage_dir if storage_dir is not None else get_default_research_storage_dir()

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise ResearchStorageError(
            f"Could not create research storage directory '{target_dir}': {err}"
        ) from err

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(package.topic)
    base_filename = f"{timestamp}_{slug}_research"
    file_path = target_dir / f"{base_filename}.json"

    counter = 1
    while file_path.exists():
        file_path = target_dir / f"{base_filename}_{counter}.json"
        counter += 1

    try:
        json_content = package.to_json(indent=2)
        file_path.write_text(json_content, encoding="utf-8")
        logger.info("Saved research package to '%s'.", file_path)
        return file_path
    except OSError as err:
        raise ResearchStorageError(
            f"Failed to write research package to '{file_path}': {err}"
        ) from err


def load_research_package(file_path: Path) -> ResearchPackage:
    """Load and validate a ResearchPackage from a JSON file.

    Args:
        file_path: Path to the research JSON file.

    Returns:
        Validated ResearchPackage instance.

    Raises:
        ResearchStorageError: If the file cannot be found, read, or validated.
    """
    if not file_path.is_file():
        raise ResearchStorageError(f"Research package file not found: '{file_path}'.")

    try:
        content = file_path.read_text(encoding="utf-8")
        return ResearchPackage.from_json(content)
    except Exception as err:
        raise ResearchStorageError(
            f"Failed to load research package from '{file_path}': {err}"
        ) from err
