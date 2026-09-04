"""Provider abstractions and mock implementations for the research engine."""

from typing import Optional, Protocol, runtime_checkable

from ai_under_60.research.models import Claim, ResearchPackage
from ai_under_60.research.request import ResearchRequest
from ai_under_60.research.web import WebResearchProvider



@runtime_checkable
class ResearchProvider(Protocol):
    """Abstract provider boundary for gathering research evidence and verifying claims."""

    def research(self, request: ResearchRequest) -> ResearchPackage:
        """Conduct research on the given request and return a ResearchPackage.

        Args:
            request: The validated research request.

        Returns:
            Validated ResearchPackage containing collected sources and claims.
        """
        ...


class MockResearchProvider:
    """Deterministic offline mock provider for testing and validation.

    Strictly adheres to project integrity rules: does not invent fake sources,
    URLs, publishers, or fabricated evidence.
    """

    def __init__(self, predefined_package: Optional[ResearchPackage] = None) -> None:
        """Initialize mock provider with an optional predefined ResearchPackage."""
        if predefined_package is not None and not isinstance(predefined_package, ResearchPackage):
            raise TypeError(
                f"Expected ResearchPackage for predefined_package, got {type(predefined_package).__name__}."
            )
        self._predefined = predefined_package

    def research(self, request: ResearchRequest) -> ResearchPackage:
        """Return a predefined package or a minimal valid ResearchPackage matching request."""
        if not isinstance(request, ResearchRequest):
            raise TypeError(f"Expected ResearchRequest instance, got {type(request).__name__}.")

        if self._predefined is not None:
            return self._predefined

        # Return an unverified ResearchPackage with zero fake sources or fake evidence
        return ResearchPackage(
            topic=request.topic,
            sources=[],
            claims=[
                Claim(
                    statement=point,
                    status="unsupported",
                    evidence=[],
                )
                for point in request.key_points
            ],
            summary=(
                f"Preliminary research package for '{request.title}'. "
                f"0 sources gathered, {len(request.key_points)} claims pending verification."
            ),
        )
