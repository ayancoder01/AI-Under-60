"""Content-idea generation engine for AI Under 60."""

import json
import re
from typing import Callable, Optional

from ai_under_60.ai.gemini import generate_text
from ai_under_60.content.models import ContentIdea, ContentValidationError
from ai_under_60.logger import setup_logger

logger = setup_logger("ai_under_60.content.idea_generator")


class IdeaGenerationError(Exception):
    """Raised when content idea generation fails due to provider or parsing issues."""


PROMPT_TEMPLATE = """You are a YouTube Shorts content strategist specializing in high-retention videos under 60 seconds.

Generate an engaging, original YouTube Shorts concept for the following topic:
TOPIC: "{topic}"

CRITICAL INSTRUCTIONS:
1. The idea MUST be suitable for a fast-paced YouTube Short strictly under 60 seconds.
2. The estimated duration must be an integer between 15 and 60 seconds.
3. You MUST respond ONLY with a raw JSON object. Do not include any explanations, markdown code blocks, backticks, or prose outside the JSON object.

REQUIRED JSON FORMAT:
{{
  "topic": "{topic}",
  "title": "Catchy YouTube Short title",
  "hook": "Attention-grabbing opening line for the first 3 seconds",
  "concept": "Core value proposition, pacing, and visual story beats",
  "target_audience": "Specific audience description",
  "estimated_duration_seconds": 45
}}
"""


def _clean_json_response(raw_text: str) -> str:
    """Strip markdown formatting or code fences if present."""
    text = raw_text.strip()
    # If the response was wrapped in markdown code blocks, strip them
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def generate_content_idea(
    topic: str,
    provider: Optional[Callable[[str], str]] = None,
) -> ContentIdea:
    """Generate a structured YouTube Short content idea for a given topic.

    Args:
        topic: The subject or theme for the content idea.
        provider: Optional text-generation function. Defaults to ai_under_60.ai.gemini.generate_text.

    Returns:
        Validated ContentIdea instance.

    Raises:
        ValueError: If topic is empty or whitespace-only.
        IdeaGenerationError: If the AI provider fails or returns malformed JSON.
        ContentValidationError: If the returned JSON does not conform to ContentIdea requirements.
    """
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic must not be empty or whitespace only.")

    clean_topic = topic.strip()
    logger.info("Generating content idea for topic: '%s'.", clean_topic)

    prompt = PROMPT_TEMPLATE.format(topic=clean_topic)
    generate_fn = provider if provider is not None else generate_text

    try:
        raw_response = generate_fn(prompt)
    except Exception as err:
        logger.error("AI provider error during content idea generation: %s", err)
        raise IdeaGenerationError(f"Content idea generation failed: {err}") from err

    cleaned_json = _clean_json_response(raw_response)

    try:
        parsed_data = json.loads(cleaned_json)
    except json.JSONDecodeError as err:
        logger.error("Failed to parse Gemini response as JSON: %s", err)
        raise IdeaGenerationError(
            f"Gemini returned malformed JSON: {err}. Raw response snippet: {raw_response[:200]!r}"
        ) from err

    if not isinstance(parsed_data, dict):
        raise IdeaGenerationError(
            f"Expected JSON object from Gemini, got {type(parsed_data).__name__}."
        )

    # Validate and construct ContentIdea
    try:
        idea = ContentIdea.from_dict(parsed_data)
    except ContentValidationError as err:
        logger.error("Generated content idea failed validation: %s", err)
        raise

    logger.info("Successfully generated content idea: '%s' (%ds).", idea.title, idea.estimated_duration_seconds)
    return idea
