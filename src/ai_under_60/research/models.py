"""Data models for research sources, evidence, claims, and packages."""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Set

VALID_CLAIM_STATUSES: Set[str] = frozenset(
    {"supported", "contradicted", "uncertain", "unsupported"}
)


class ResearchValidationError(ValueError):
    """Raised when a research data model fails validation rules."""


VALID_SOURCE_QUALITIES: Set[str] = frozenset({
    "primary", "reputable_secondary", "general_secondary", "user_generated", "unknown"
})


@dataclass(frozen=True)
class Source:
    """Represents an external reference source retrieved or supplied for research."""

    title: str
    url: str
    publisher: str
    retrieved_at: str
    source_quality: str = "unknown"

    def __post_init__(self) -> None:
        """Validate source fields."""
        if not isinstance(self.title, str) or not self.title.strip():
            raise ResearchValidationError("Source title must be a non-empty string.")

        if not isinstance(self.url, str) or not self.url.strip():
            raise ResearchValidationError("Source url must be a non-empty string.")

        if not isinstance(self.publisher, str) or not self.publisher.strip():
            raise ResearchValidationError("Source publisher must be a non-empty string.")

        if not isinstance(self.retrieved_at, str) or not self.retrieved_at.strip():
            raise ResearchValidationError("Source retrieved_at must be a non-empty string.")

        if not isinstance(self.source_quality, str) or self.source_quality not in VALID_SOURCE_QUALITIES:
            allowed = ", ".join(sorted(VALID_SOURCE_QUALITIES))
            raise ResearchValidationError(
                f"Source source_quality must be one of [{allowed}], got '{self.source_quality}'."
            )

    def to_dict(self) -> Dict[str, str]:
        """Convert Source to a plain dictionary."""
        return {
            "title": self.title.strip(),
            "url": self.url.strip(),
            "publisher": self.publisher.strip(),
            "retrieved_at": self.retrieved_at.strip(),
            "source_quality": self.source_quality,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Source":
        """Construct and validate a Source from a dictionary."""
        if not isinstance(data, dict):
            raise ResearchValidationError(
                f"Source data must be a dictionary, got {type(data).__name__}."
            )

        required = {"title", "url", "publisher", "retrieved_at"}
        missing = required - set(data.keys())
        if missing:
            raise ResearchValidationError(
                f"Missing required field(s) in Source: {', '.join(sorted(missing))}."
            )

        return cls(
            title=data["title"],
            url=data["url"],
            publisher=data["publisher"],
            retrieved_at=data["retrieved_at"],
            source_quality=data.get("source_quality", "unknown"),
        )


@dataclass(frozen=True)
class Evidence:
    """Represents a factual excerpt extracted from a source to substantiate or refute claims."""

    source_url: str
    excerpt: str
    relevance: str

    def __post_init__(self) -> None:
        """Validate evidence fields."""
        if not isinstance(self.source_url, str) or not self.source_url.strip():
            raise ResearchValidationError("Evidence source_url must be a non-empty string.")

        if not isinstance(self.excerpt, str) or not self.excerpt.strip():
            raise ResearchValidationError("Evidence excerpt must be a non-empty string.")

        if not isinstance(self.relevance, str) or not self.relevance.strip():
            raise ResearchValidationError("Evidence relevance must be a non-empty string.")

    def to_dict(self) -> Dict[str, str]:
        """Convert Evidence to a plain dictionary."""
        return {
            "source_url": self.source_url.strip(),
            "excerpt": self.excerpt.strip(),
            "relevance": self.relevance.strip(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        """Construct and validate an Evidence instance from a dictionary."""
        if not isinstance(data, dict):
            raise ResearchValidationError(
                f"Evidence data must be a dictionary, got {type(data).__name__}."
            )

        required = {"source_url", "excerpt", "relevance"}
        missing = required - set(data.keys())
        if missing:
            raise ResearchValidationError(
                f"Missing required field(s) in Evidence: {', '.join(sorted(missing))}."
            )

        return cls(
            source_url=data["source_url"],
            excerpt=data["excerpt"],
            relevance=data["relevance"],
        )


@dataclass(frozen=True)
class Claim:
    """Represents a factual statement that requires verification against collected evidence."""

    statement: str
    status: str
    evidence: List[Evidence] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate claim fields."""
        if not isinstance(self.statement, str) or not self.statement.strip():
            raise ResearchValidationError("Claim statement must be a non-empty string.")

        if not isinstance(self.status, str) or self.status.strip().lower() not in VALID_CLAIM_STATUSES:
            allowed = ", ".join(sorted(VALID_CLAIM_STATUSES))
            raise ResearchValidationError(
                f"Claim status must be one of [{allowed}], got '{self.status}'."
            )

        if not isinstance(self.evidence, list):
            raise ResearchValidationError(
                f"Claim evidence must be a list of Evidence objects, got {type(self.evidence).__name__}."
            )

        for idx, item in enumerate(self.evidence):
            if not isinstance(item, Evidence):
                raise ResearchValidationError(
                    f"Claim evidence item at index {idx} must be an Evidence instance, got {type(item).__name__}."
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Claim to a dictionary."""
        return {
            "statement": self.statement.strip(),
            "status": self.status.strip().lower(),
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Claim":
        """Construct and validate a Claim from a dictionary."""
        if not isinstance(data, dict):
            raise ResearchValidationError(
                f"Claim data must be a dictionary, got {type(data).__name__}."
            )

        required = {"statement", "status"}
        missing = required - set(data.keys())
        if missing:
            raise ResearchValidationError(
                f"Missing required field(s) in Claim: {', '.join(sorted(missing))}."
            )

        raw_evidence = data.get("evidence", [])
        if not isinstance(raw_evidence, list):
            raise ResearchValidationError(
                f"Claim evidence must be a list, got {type(raw_evidence).__name__}."
            )

        parsed_evidence: List[Evidence] = []
        for idx, item in enumerate(raw_evidence):
            if isinstance(item, Evidence):
                parsed_evidence.append(item)
            elif isinstance(item, dict):
                try:
                    parsed_evidence.append(Evidence.from_dict(item))
                except ResearchValidationError as err:
                    raise ResearchValidationError(
                        f"Invalid Evidence item in Claim at index {idx}: {err}"
                    ) from err
            else:
                raise ResearchValidationError(
                    f"Evidence at index {idx} must be an Evidence instance or dict, got {type(item).__name__}."
                )

        return cls(
            statement=data["statement"],
            status=data["status"],
            evidence=parsed_evidence,
        )


@dataclass(frozen=True)
class ResearchPackage:
    """Encapsulates the complete findings of a research inquiry."""

    topic: str
    sources: List[Source] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    summary: str = ""

    def __post_init__(self) -> None:
        """Validate research package fields."""
        if not isinstance(self.topic, str) or not self.topic.strip():
            raise ResearchValidationError("ResearchPackage topic must be a non-empty string.")

        if not isinstance(self.sources, list):
            raise ResearchValidationError(
                f"ResearchPackage sources must be a list of Source objects, got {type(self.sources).__name__}."
            )

        for idx, s in enumerate(self.sources):
            if not isinstance(s, Source):
                raise ResearchValidationError(
                    f"ResearchPackage source at index {idx} must be a Source instance, got {type(s).__name__}."
                )

        if not isinstance(self.claims, list):
            raise ResearchValidationError(
                f"ResearchPackage claims must be a list of Claim objects, got {type(self.claims).__name__}."
            )

        for idx, c in enumerate(self.claims):
            if not isinstance(c, Claim):
                raise ResearchValidationError(
                    f"ResearchPackage claim at index {idx} must be a Claim instance, got {type(c).__name__}."
                )

        if not isinstance(self.summary, str):
            raise ResearchValidationError(
                f"ResearchPackage summary must be a string, got {type(self.summary).__name__}."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResearchPackage to a plain dictionary."""
        return {
            "topic": self.topic.strip(),
            "sources": [s.to_dict() for s in self.sources],
            "claims": [c.to_dict() for c in self.claims],
            "summary": self.summary.strip(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize ResearchPackage to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchPackage":
        """Construct and validate a ResearchPackage from a dictionary."""
        if not isinstance(data, dict):
            raise ResearchValidationError(
                f"ResearchPackage data must be a dictionary, got {type(data).__name__}."
            )

        if "topic" not in data:
            raise ResearchValidationError("Missing required field 'topic' in ResearchPackage.")

        raw_sources = data.get("sources", [])
        if not isinstance(raw_sources, list):
            raise ResearchValidationError(
                f"ResearchPackage sources must be a list, got {type(raw_sources).__name__}."
            )

        parsed_sources: List[Source] = []
        for idx, item in enumerate(raw_sources):
            if isinstance(item, Source):
                parsed_sources.append(item)
            elif isinstance(item, dict):
                try:
                    parsed_sources.append(Source.from_dict(item))
                except ResearchValidationError as err:
                    raise ResearchValidationError(
                        f"Invalid Source item in ResearchPackage at index {idx}: {err}"
                    ) from err
            else:
                raise ResearchValidationError(
                    f"Source at index {idx} must be a Source instance or dict, got {type(item).__name__}."
                )

        raw_claims = data.get("claims", [])
        if not isinstance(raw_claims, list):
            raise ResearchValidationError(
                f"ResearchPackage claims must be a list, got {type(raw_claims).__name__}."
            )

        parsed_claims: List[Claim] = []
        for idx, item in enumerate(raw_claims):
            if isinstance(item, Claim):
                parsed_claims.append(item)
            elif isinstance(item, dict):
                try:
                    parsed_claims.append(Claim.from_dict(item))
                except ResearchValidationError as err:
                    raise ResearchValidationError(
                        f"Invalid Claim item in ResearchPackage at index {idx}: {err}"
                    ) from err
            else:
                raise ResearchValidationError(
                    f"Claim at index {idx} must be a Claim instance or dict, got {type(item).__name__}."
                )

        summary = data.get("summary", "")
        if not isinstance(summary, str):
            raise ResearchValidationError(
                f"ResearchPackage summary must be a string, got {type(summary).__name__}."
            )

        return cls(
            topic=data["topic"],
            sources=parsed_sources,
            claims=parsed_claims,
            summary=summary,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ResearchPackage":
        """Construct and validate a ResearchPackage from a JSON string."""
        if not isinstance(json_str, str) or not json_str.strip():
            raise ResearchValidationError("Input JSON string must not be empty.")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as err:
            raise ResearchValidationError(f"Malformed JSON for ResearchPackage: {err}") from err

        return cls.from_dict(data)
