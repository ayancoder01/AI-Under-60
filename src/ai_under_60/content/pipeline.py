"""Orchestration pipeline for AI Under 60 content generation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ai_under_60.content.brief import content_idea_to_brief
from ai_under_60.content.idea_generator import generate_content_idea
from ai_under_60.content.models import (
    ContentBrief,
    ContentIdea,
    ContentValidationError,
)
from ai_under_60.content.storage import (
    StorageError,
    save_content_brief,
    save_content_idea,
)
from ai_under_60.logger import setup_logger

logger = setup_logger("ai_under_60.content.pipeline")


class PipelineError(Exception):
    """Raised when any step of the content generation pipeline fails."""


@dataclass(frozen=True)
class PipelineResult:
    """Encapsulates the structured outputs and saved file paths of the pipeline."""

    idea: ContentIdea
    brief: ContentBrief
    idea_path: Path
    brief_path: Path

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the pipeline outputs."""
        return {
            "idea": self.idea.to_dict(),
            "brief": self.brief.to_dict(),
            "idea_path": str(self.idea_path),
            "brief_path": str(self.brief_path),
        }


def run_content_pipeline(
    topic: str,
    provider: Optional[Callable[[str], str]] = None,
    call_to_action: Optional[str] = None,
    ideas_storage_dir: Optional[Path] = None,
    briefs_storage_dir: Optional[Path] = None,
) -> PipelineResult:
    """Execute the end-to-end content generation pipeline for a topic.

    Steps:
    1. Validate non-empty topic.
    2. Generate structured ContentIdea via idea_generator.
    3. Validate ContentIdea.
    4. Convert ContentIdea into structured ContentBrief via brief module.
    5. Validate ContentBrief.
    6. Persist ContentIdea to JSON storage.
    7. Persist ContentBrief to JSON storage.
    8. Return PipelineResult with artifacts and file paths.

    Args:
        topic: The video topic/subject string.
        provider: Optional AI generation function (for test mocking/injection).
        call_to_action: Optional custom call-to-action string.
        ideas_storage_dir: Optional custom directory for saving idea artifacts.
        briefs_storage_dir: Optional custom directory for saving brief artifacts.

    Returns:
        PipelineResult containing the validated idea, brief, and their saved paths.

    Raises:
        ValueError: If topic is empty or whitespace-only.
        PipelineError: If generation, validation, conversion, or persistence fails.
    """
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic must be a non-empty string.")

    clean_topic = topic.strip()
    logger.info("Starting content generation pipeline for topic: '%s'.", clean_topic)

    # 1. Generate ContentIdea
    try:
        idea = generate_content_idea(clean_topic, provider=provider)
    except (ValueError, ContentValidationError) as err:
        logger.error("ContentIdea validation failed: %s", err)
        raise PipelineError(f"Content idea validation failed: {err}") from err
    except Exception as err:
        logger.error("ContentIdea generation failed: %s", err)
        raise PipelineError(f"Content idea generation failed: {err}") from err

    if not isinstance(idea, ContentIdea):
        raise PipelineError(f"Expected ContentIdea, got {type(idea).__name__}.")

    # 2. Convert to ContentBrief
    try:
        brief = content_idea_to_brief(idea, call_to_action=call_to_action)
    except ContentValidationError as err:
        logger.error("ContentBrief validation failed: %s", err)
        raise PipelineError(f"Content brief validation failed: {err}") from err
    except Exception as err:
        logger.error("ContentBrief conversion failed: %s", err)
        raise PipelineError(f"Content brief conversion failed: {err}") from err

    if not isinstance(brief, ContentBrief):
        raise PipelineError(f"Expected ContentBrief, got {type(brief).__name__}.")

    # 3. Persist ContentIdea
    try:
        idea_path = save_content_idea(idea, storage_dir=ideas_storage_dir)
    except StorageError as err:
        logger.error("Failed to save ContentIdea: %s", err)
        raise PipelineError(f"Failed to persist content idea: {err}") from err
    except Exception as err:
        logger.error("Unexpected error saving ContentIdea: %s", err)
        raise PipelineError(f"Failed to persist content idea: {err}") from err

    # 4. Persist ContentBrief
    try:
        brief_path = save_content_brief(brief, storage_dir=briefs_storage_dir)
    except StorageError as err:
        logger.error("Failed to save ContentBrief: %s", err)
        raise PipelineError(f"Failed to persist content brief: {err}") from err
    except Exception as err:
        logger.error("Unexpected error saving ContentBrief: %s", err)
        raise PipelineError(f"Failed to persist content brief: {err}") from err

    logger.info(
        "Pipeline completed successfully. Idea saved to '%s', Brief saved to '%s'.",
        idea_path,
        brief_path,
    )

    return PipelineResult(
        idea=idea,
        brief=brief,
        idea_path=idea_path,
        brief_path=brief_path,
    )
