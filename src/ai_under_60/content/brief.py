"""Conversion and processing logic for structured content briefs."""

import re
from typing import List, Optional

from ai_under_60.content.models import ContentBrief, ContentIdea
from ai_under_60.logger import setup_logger

logger = setup_logger("ai_under_60.content.brief")

DEFAULT_CALL_TO_ACTION = "Follow @AIUnder60 for more AI insights in under 60 seconds!"


def extract_key_points_from_concept(concept: str) -> List[str]:
    """Derive a list of concise key points from a concept description.

    Heuristics:
    1. Splits on explicit beat markers (e.g., 'Visual Beat 1:', 'Beat 1:', 'Step 1:', '1.').
    2. If no beat markers are found, splits on sentence and clause boundaries (periods, semicolons, newlines).
    3. Strips trailing punctuation, whitespace, and empty entries.
    4. Guarantees at least 1 non-empty key point.

    Args:
        concept: The narrative concept string.

    Returns:
        List of concise key point strings.
    """
    if not concept or not concept.strip():
        return ["Overview of the core concept"]

    text = concept.strip()

    # Pattern for explicit beat/step markers: e.g. "Visual Beat 1:", "Beat 1:", "Step 1:", "1. "
    marker_pattern = r"(?:Visual Beat \d+:?|Beat \d+:?|Final Beat:?|Step \d+:?|\b\d+\.\s+)"
    if re.search(marker_pattern, text, re.IGNORECASE):
        parts = re.split(marker_pattern, text, flags=re.IGNORECASE)
        points = [p.strip().rstrip(".;,") for p in parts if p.strip()]
        if points:
            return points

    # Fallback: split on sentence boundaries (. ; or newline followed by space or end)
    sentence_pattern = r"(?:[.;\n]+(?:\s+|$))"
    parts = re.split(sentence_pattern, text)
    points = [p.strip().rstrip(".;,") for p in parts if p.strip()]
    if points:
        return points

    return [text]


def content_idea_to_brief(
    idea: ContentIdea,
    call_to_action: Optional[str] = None,
) -> ContentBrief:
    """Convert an existing ContentIdea into a validated ContentBrief.

    This conversion is fully deterministic and does not make external API calls.

    Args:
        idea: Validated ContentIdea instance.
        call_to_action: Optional custom call to action. If omitted, uses standard default.

    Returns:
        Validated ContentBrief instance.

    Raises:
        TypeError: If idea is not an instance of ContentIdea.
        ContentValidationError: If the resulting brief fails validation.
    """
    if not isinstance(idea, ContentIdea):
        raise TypeError(f"Expected ContentIdea instance, got {type(idea).__name__}.")

    cta = call_to_action.strip() if call_to_action and call_to_action.strip() else DEFAULT_CALL_TO_ACTION
    key_points = extract_key_points_from_concept(idea.concept)

    logger.debug("Converting ContentIdea '%s' to ContentBrief (%d points).", idea.title, len(key_points))

    return ContentBrief(
        topic=idea.topic,
        title=idea.title,
        hook=idea.hook,
        concept=idea.concept,
        target_audience=idea.target_audience,
        estimated_duration_seconds=idea.estimated_duration_seconds,
        key_points=key_points,
        call_to_action=cta,
    )
