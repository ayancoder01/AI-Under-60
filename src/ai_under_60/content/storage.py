"""Storage layer for saving and retrieving generated content ideas."""

from datetime import datetime
import os
from pathlib import Path
import re
from typing import Optional

from ai_under_60.config import get_config
from ai_under_60.content.models import ContentIdea
from ai_under_60.logger import setup_logger

logger = setup_logger("ai_under_60.content.storage")


class StorageError(Exception):
    """Raised when storing or loading content ideas fails."""


def _slugify(text: str, max_length: int = 40) -> str:
    """Convert a topic string into a safe, clean filename slug."""
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    return slug[:max_length].strip("_") or "content_idea"


def get_default_storage_dir() -> Path:
    """Get the default runtime directory for storing content ideas."""
    config = get_config()
    return config.project_root / "data" / "content_ideas"


def save_content_idea(
    idea: ContentIdea,
    storage_dir: Optional[Path] = None,
) -> Path:
    """Save a ContentIdea instance to a JSON file.

    Args:
        idea: Validated ContentIdea instance.
        storage_dir: Optional target directory. Defaults to <project_root>/data/content_ideas.

    Returns:
        Path to the saved JSON file.

    Raises:
        StorageError: If the file cannot be written.
    """
    if not isinstance(idea, ContentIdea):
        raise StorageError(f"Expected ContentIdea instance, got {type(idea).__name__}.")

    target_dir = storage_dir if storage_dir is not None else get_default_storage_dir()

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise StorageError(f"Could not create storage directory '{target_dir}': {err}") from err

    # Create safe, unique filename using timestamp and slugified topic
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(idea.topic)
    base_filename = f"{timestamp}_{slug}"
    file_path = target_dir / f"{base_filename}.json"

    # Avoid accidental overwrite if file with same name already exists
    counter = 1
    while file_path.exists():
        file_path = target_dir / f"{base_filename}_{counter}.json"
        counter += 1

    try:
        json_content = idea.to_json(indent=2)
        file_path.write_text(json_content, encoding="utf-8")
        logger.info("Saved content idea to '%s'.", file_path)
        return file_path
    except OSError as err:
        raise StorageError(f"Failed to write content idea to '{file_path}': {err}") from err


def load_content_idea(file_path: Path) -> ContentIdea:
    """Load and validate a ContentIdea from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Validated ContentIdea instance.

    Raises:
        StorageError: If the file cannot be read or contains invalid data.
    """
    if not file_path.is_file():
        raise StorageError(f"Content idea file not found: '{file_path}'.")

    try:
        content = file_path.read_text(encoding="utf-8")
        return ContentIdea.from_json(content)
    except Exception as err:
        raise StorageError(f"Failed to load content idea from '{file_path}': {err}") from err
