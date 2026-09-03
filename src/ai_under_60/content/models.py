"""Data models for content generation in AI Under 60."""

from dataclasses import asdict, dataclass
import json
from typing import Any, Dict


class ContentValidationError(ValueError):
    """Raised when a ContentIdea fails validation rules."""


@dataclass(frozen=True)
class ContentIdea:
    """Structured representation of a video content idea under 60 seconds."""

    topic: str
    title: str
    hook: str
    concept: str
    target_audience: str
    estimated_duration_seconds: int

    def __post_init__(self) -> None:
        """Validate content idea fields."""
        # 1. Validate topic
        if not isinstance(self.topic, str) or not self.topic.strip():
            raise ContentValidationError("Topic must be a non-empty string.")

        # 2. Validate title
        if not isinstance(self.title, str) or not self.title.strip():
            raise ContentValidationError("Title must be a non-empty string.")

        # 3. Validate hook
        if not isinstance(self.hook, str) or not self.hook.strip():
            raise ContentValidationError("Hook must be a non-empty string.")

        # 4. Validate concept
        if not isinstance(self.concept, str) or not self.concept.strip():
            raise ContentValidationError("Concept must be a non-empty string.")

        # 5. Validate target_audience
        if not isinstance(self.target_audience, str) or not self.target_audience.strip():
            raise ContentValidationError("Target audience must be a non-empty string.")

        # 6. Validate estimated_duration_seconds
        # In Python, bool is a subclass of int (isinstance(True, int) == True)
        if type(self.estimated_duration_seconds) is not int:
            raise ContentValidationError(
                f"estimated_duration_seconds must be an integer, got "
                f"{type(self.estimated_duration_seconds).__name__}."
            )

        if self.estimated_duration_seconds <= 0:
            raise ContentValidationError("estimated_duration_seconds must be greater than 0.")

        if self.estimated_duration_seconds > 60:
            raise ContentValidationError(
                f"estimated_duration_seconds must not exceed 60 seconds for AI Under 60, "
                f"got {self.estimated_duration_seconds}."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the content idea to a plain dictionary."""
        return {
            "topic": self.topic.strip(),
            "title": self.title.strip(),
            "hook": self.hook.strip(),
            "concept": self.concept.strip(),
            "target_audience": self.target_audience.strip(),
            "estimated_duration_seconds": self.estimated_duration_seconds,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the content idea to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Any) -> "ContentIdea":
        """Construct and validate a ContentIdea from a dictionary.

        Args:
            data: Dictionary containing content idea attributes.

        Returns:
            Validated ContentIdea instance.

        Raises:
            ContentValidationError: If data is not a dict, missing keys, or has invalid types.
        """
        if not isinstance(data, dict):
            raise ContentValidationError(f"Expected dictionary for content idea, got {type(data).__name__}.")

        required_keys = {
            "topic",
            "title",
            "hook",
            "concept",
            "target_audience",
            "estimated_duration_seconds",
        }
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ContentValidationError(
                f"Missing required field(s) in content idea: {', '.join(sorted(missing_keys))}."
            )

        return cls(
            topic=str(data["topic"]).strip(),
            title=str(data["title"]).strip(),
            hook=str(data["hook"]).strip(),
            concept=str(data["concept"]).strip(),
            target_audience=str(data["target_audience"]).strip(),
            estimated_duration_seconds=data["estimated_duration_seconds"],
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ContentIdea":
        """Construct and validate a ContentIdea from a JSON string.

        Args:
            json_str: JSON string containing content idea fields.

        Returns:
            Validated ContentIdea instance.

        Raises:
            ContentValidationError: If JSON is malformed or validation fails.
        """
        if not isinstance(json_str, str) or not json_str.strip():
            raise ContentValidationError("Input JSON string must not be empty.")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as err:
            raise ContentValidationError(f"Malformed JSON for content idea: {err}") from err

        return cls.from_dict(data)
