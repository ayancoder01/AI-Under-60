"""Research request model and conversion from ContentBrief."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai_under_60.content.models import ContentBrief
from ai_under_60.research.models import ResearchValidationError


@dataclass(frozen=True)
class ResearchRequest:
    """Represents a structured request for fact-checking and evidence gathering."""

    topic: str
    title: str
    key_points: List[str]
    context: str = ""

    def __post_init__(self) -> None:
        """Validate research request fields."""
        if not isinstance(self.topic, str) or not self.topic.strip():
            raise ResearchValidationError("ResearchRequest topic must be a non-empty string.")

        if not isinstance(self.title, str) or not self.title.strip():
            raise ResearchValidationError("ResearchRequest title must be a non-empty string.")

        if not isinstance(self.key_points, list):
            raise ResearchValidationError(
                f"ResearchRequest key_points must be a list, got {type(self.key_points).__name__}."
            )

        if len(self.key_points) == 0:
            raise ResearchValidationError("ResearchRequest key_points must contain at least 1 item.")

        for idx, item in enumerate(self.key_points):
            if not isinstance(item, str) or not item.strip():
                raise ResearchValidationError(
                    f"ResearchRequest key_point at index {idx} must be a non-empty string."
                )

        if not isinstance(self.context, str):
            raise ResearchValidationError(
                f"ResearchRequest context must be a string, got {type(self.context).__name__}."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResearchRequest to a plain dictionary."""
        return {
            "topic": self.topic.strip(),
            "title": self.title.strip(),
            "key_points": [p.strip() for p in self.key_points],
            "context": self.context.strip(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchRequest":
        """Construct and validate a ResearchRequest from a dictionary."""
        if not isinstance(data, dict):
            raise ResearchValidationError(
                f"ResearchRequest data must be a dictionary, got {type(data).__name__}."
            )

        required = {"topic", "title", "key_points"}
        missing = required - set(data.keys())
        if missing:
            raise ResearchValidationError(
                f"Missing required field(s) in ResearchRequest: {', '.join(sorted(missing))}."
            )

        return cls(
            topic=data["topic"],
            title=data["title"],
            key_points=data["key_points"],
            context=data.get("context", ""),
        )


def create_research_request(brief: ContentBrief) -> ResearchRequest:
    """Convert an existing ContentBrief into a deterministic ResearchRequest.

    This function does not perform any network calls.

    Args:
        brief: Validated ContentBrief instance.

    Returns:
        Validated ResearchRequest instance.

    Raises:
        TypeError: If brief is not an instance of ContentBrief.
        ResearchValidationError: If request validation fails.
    """
    if not isinstance(brief, ContentBrief):
        raise TypeError(f"Expected ContentBrief instance, got {type(brief).__name__}.")

    return ResearchRequest(
        topic=brief.topic,
        title=brief.title,
        key_points=list(brief.key_points),
        context=brief.concept,
    )
