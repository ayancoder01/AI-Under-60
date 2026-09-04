"""Unit tests for the research engine foundation models, storage, request, and provider boundary."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.content.models import ContentBrief
from ai_under_60.research.models import (
    VALID_CLAIM_STATUSES,
    Claim,
    Evidence,
    ResearchPackage,
    ResearchValidationError,
    Source,
)
from ai_under_60.research.provider import (
    MockResearchProvider,
    ResearchProvider,
)
from ai_under_60.research.request import (
    ResearchRequest,
    create_research_request,
)
from ai_under_60.research.storage import (
    ResearchStorageError,
    _slugify,
    get_default_research_storage_dir,
    load_research_package,
    save_research_package,
)


class TestResearchModels(unittest.TestCase):
    """Test suite for research data models: Source, Evidence, Claim, and ResearchPackage."""

    # ------------------------------------------------------------------
    # Source tests
    # ------------------------------------------------------------------

    def test_valid_source(self) -> None:
        """Verify Source constructs and serializes correctly with valid data."""
        source = Source(
            title="State of AI Report 2025",
            url="https://example.com/state-of-ai-2025",
            publisher="AI Research Institute",
            retrieved_at="2026-09-04T12:00:00Z",
        )
        self.assertEqual(source.title, "State of AI Report 2025")
        self.assertEqual(source.url, "https://example.com/state-of-ai-2025")
        self.assertEqual(source.publisher, "AI Research Institute")
        self.assertEqual(source.retrieved_at, "2026-09-04T12:00:00Z")

        # Serialization round-trip
        data = source.to_dict()
        self.assertEqual(Source.from_dict(data), source)

    def test_source_empty_fields_raise_validation_error(self) -> None:
        """Verify empty or non-string fields in Source raise ResearchValidationError."""
        valid_kwargs = {
            "title": "Valid Title",
            "url": "https://example.com",
            "publisher": "Valid Publisher",
            "retrieved_at": "2026-09-04T00:00:00Z",
        }

        for field in ["title", "url", "publisher", "retrieved_at"]:
            for bad_val in ["", "   ", None, 123]:
                with self.subTest(field=field, bad_val=bad_val):
                    kwargs = valid_kwargs.copy()
                    kwargs[field] = bad_val
                    with self.assertRaises(ResearchValidationError):
                        Source(**kwargs)

    def test_source_from_dict_missing_fields(self) -> None:
        """Verify Source.from_dict raises error when required fields are missing."""
        with self.assertRaises(ResearchValidationError):
            Source.from_dict({"title": "Only title"})

        with self.assertRaises(ResearchValidationError):
            Source.from_dict("not a dict")  # type: ignore

    # ------------------------------------------------------------------
    # Evidence tests
    # ------------------------------------------------------------------

    def test_valid_evidence(self) -> None:
        """Verify Evidence constructs and serializes correctly."""
        evidence = Evidence(
            source_url="https://example.com/report",
            excerpt="AI agents handled 42% of tier-1 customer inquiries autonomously.",
            relevance="Demonstrates current enterprise autonomy rates.",
        )
        self.assertEqual(evidence.source_url, "https://example.com/report")
        self.assertEqual(evidence.excerpt, "AI agents handled 42% of tier-1 customer inquiries autonomously.")
        self.assertEqual(evidence.relevance, "Demonstrates current enterprise autonomy rates.")

        # Serialization round-trip
        data = evidence.to_dict()
        self.assertEqual(Evidence.from_dict(data), evidence)

    def test_evidence_empty_fields_raise_validation_error(self) -> None:
        """Verify empty or non-string fields in Evidence raise ResearchValidationError."""
        valid_kwargs = {
            "source_url": "https://example.com",
            "excerpt": "Evidence excerpt",
            "relevance": "Direct relevance",
        }

        for field in ["source_url", "excerpt", "relevance"]:
            for bad_val in ["", "   ", None, 456]:
                with self.subTest(field=field, bad_val=bad_val):
                    kwargs = valid_kwargs.copy()
                    kwargs[field] = bad_val
                    with self.assertRaises(ResearchValidationError):
                        Evidence(**kwargs)

    def test_evidence_from_dict_invalid(self) -> None:
        """Verify Evidence.from_dict raises error on non-dict or missing fields."""
        with self.assertRaises(ResearchValidationError):
            Evidence.from_dict({"source_url": "https://example.com"})

        with self.assertRaises(ResearchValidationError):
            Evidence.from_dict(["not", "a", "dict"])  # type: ignore

    # ------------------------------------------------------------------
    # Claim tests
    # ------------------------------------------------------------------

    def test_valid_claims_all_statuses(self) -> None:
        """Verify Claim accepts each of the four valid statuses."""
        ev = Evidence(
            source_url="https://example.com",
            excerpt="Test excerpt",
            relevance="High",
        )

        for status in VALID_CLAIM_STATUSES:
            with self.subTest(status=status):
                claim = Claim(
                    statement="AI agents automate multi-step tasks.",
                    status=status,
                    evidence=[ev] if status == "supported" else [],
                )
                self.assertEqual(claim.status, status)
                self.assertEqual(claim.statement, "AI agents automate multi-step tasks.")

                # Serialization round-trip
                data = claim.to_dict()
                restored = Claim.from_dict(data)
                self.assertEqual(restored, claim)

    def test_claim_invalid_status_raises_error(self) -> None:
        """Verify invalid claim statuses raise ResearchValidationError."""
        for invalid_status in ["verified", "true", "false", "confirmed", "unknown", ""]:
            with self.subTest(invalid_status=invalid_status):
                with self.assertRaises(ResearchValidationError):
                    Claim(
                        statement="Valid statement",
                        status=invalid_status,
                    )

    def test_claim_empty_statement_raises_error(self) -> None:
        """Verify empty statement raises ResearchValidationError."""
        for bad_statement in ["", "   ", None, 789]:
            with self.subTest(bad_statement=bad_statement):
                with self.assertRaises(ResearchValidationError):
                    Claim(statement=bad_statement, status="unsupported")  # type: ignore

    def test_claim_evidence_validation(self) -> None:
        """Verify evidence must be a list of Evidence objects."""
        # Non-list evidence
        with self.assertRaises(ResearchValidationError):
            Claim(statement="Statement", status="unsupported", evidence="not a list")  # type: ignore

        # List with non-Evidence items
        with self.assertRaises(ResearchValidationError):
            Claim(statement="Statement", status="unsupported", evidence=["not an Evidence object"])  # type: ignore

    def test_claim_from_dict_nested_evidence(self) -> None:
        """Verify Claim.from_dict properly parses nested evidence dicts."""
        data = {
            "statement": "Autonomous agents execute tasks.",
            "status": "supported",
            "evidence": [
                {
                    "source_url": "https://example.com",
                    "excerpt": "Evidence excerpt",
                    "relevance": "High relevance",
                }
            ],
        }
        claim = Claim.from_dict(data)
        self.assertEqual(len(claim.evidence), 1)
        self.assertIsInstance(claim.evidence[0], Evidence)
        self.assertEqual(claim.evidence[0].source_url, "https://example.com")

    # ------------------------------------------------------------------
    # ResearchPackage tests
    # ------------------------------------------------------------------

    def test_valid_research_package(self) -> None:
        """Verify ResearchPackage constructs, validates, and serializes to/from JSON."""
        source = Source(
            title="Tech Analysis",
            url="https://example.com/tech",
            publisher="Tech Journal",
            retrieved_at="2026-09-04T00:00:00Z",
        )
        evidence = Evidence(
            source_url="https://example.com/tech",
            excerpt="Key insight on agents.",
            relevance="Substantiates title claim.",
        )
        claim = Claim(
            statement="Agents are autonomous.",
            status="supported",
            evidence=[evidence],
        )

        package = ResearchPackage(
            topic="Why AI agents are becoming popular",
            sources=[source],
            claims=[claim],
            summary="Thorough analysis of AI agent autonomy.",
        )

        self.assertEqual(package.topic, "Why AI agents are becoming popular")
        self.assertEqual(len(package.sources), 1)
        self.assertEqual(len(package.claims), 1)
        self.assertEqual(package.summary, "Thorough analysis of AI agent autonomy.")

        # JSON round-trip
        json_str = package.to_json()
        restored = ResearchPackage.from_json(json_str)
        self.assertEqual(restored, package)

    def test_research_package_empty_topic_raises_error(self) -> None:
        """Verify empty topic raises ResearchValidationError."""
        for bad_topic in ["", "   ", None, 123]:
            with self.subTest(bad_topic=bad_topic):
                with self.assertRaises(ResearchValidationError):
                    ResearchPackage(topic=bad_topic)  # type: ignore

    def test_research_package_invalid_sources_or_claims(self) -> None:
        """Verify invalid sources or claims raise ResearchValidationError."""
        with self.assertRaises(ResearchValidationError):
            ResearchPackage(topic="Topic", sources="not a list")  # type: ignore

        with self.assertRaises(ResearchValidationError):
            ResearchPackage(topic="Topic", sources=["not a Source"])  # type: ignore

        with self.assertRaises(ResearchValidationError):
            ResearchPackage(topic="Topic", claims="not a list")  # type: ignore

        with self.assertRaises(ResearchValidationError):
            ResearchPackage(topic="Topic", claims=["not a Claim"])  # type: ignore

        with self.assertRaises(ResearchValidationError):
            ResearchPackage(topic="Topic", summary=123)  # type: ignore

    def test_research_package_from_json_malformed(self) -> None:
        """Verify malformed JSON raises ResearchValidationError."""
        with self.assertRaises(ResearchValidationError):
            ResearchPackage.from_json("")

        with self.assertRaises(ResearchValidationError):
            ResearchPackage.from_json("invalid json {")

        with self.assertRaises(ResearchValidationError):
            ResearchPackage.from_json(json.dumps(["not", "a", "dict"]))


class TestResearchRequest(unittest.TestCase):
    """Test suite for ResearchRequest and ContentBrief conversion."""

    def setUp(self) -> None:
        """Create sample ContentBrief for conversion tests."""
        self.brief = ContentBrief(
            topic="Why AI agents are becoming popular",
            title="Why Chatbots Are DEAD (Meet AI Agents)",
            hook="Stop asking ChatGPT questions—that's already outdated.",
            concept="Split-screen contrasting chatbots with agents.",
            target_audience="Tech enthusiasts",
            estimated_duration_seconds=45,
            key_points=[
                "Chatbots only talk, AI agents take action",
                "Agents browse flight sites and book trips autonomously",
                "Companies are investing billions into autonomous execution",
            ],
            call_to_action="Follow @AIUnder60 for more!",
        )

    def test_create_research_request_from_brief(self) -> None:
        """Verify create_research_request deterministically extracts required fields."""
        req = create_research_request(self.brief)

        self.assertIsInstance(req, ResearchRequest)
        self.assertEqual(req.topic, self.brief.topic)
        self.assertEqual(req.title, self.brief.title)
        self.assertEqual(req.key_points, self.brief.key_points)
        self.assertEqual(req.context, self.brief.concept)

        # Ensure deterministic
        req2 = create_research_request(self.brief)
        self.assertEqual(req, req2)

    def test_create_research_request_type_error(self) -> None:
        """Verify passing non-ContentBrief raises TypeError."""
        with self.assertRaises(TypeError):
            create_research_request({"topic": "Invalid"}  # type: ignore
            )

    def test_research_request_validation(self) -> None:
        """Verify ResearchRequest validation checks."""
        # Empty topic
        with self.assertRaises(ResearchValidationError):
            ResearchRequest(topic="", title="Title", key_points=["Point 1"])

        # Empty title
        with self.assertRaises(ResearchValidationError):
            ResearchRequest(topic="Topic", title="", key_points=["Point 1"])

        # Empty key_points list
        with self.assertRaises(ResearchValidationError):
            ResearchRequest(topic="Topic", title="Title", key_points=[])

        # Key point with empty string
        with self.assertRaises(ResearchValidationError):
            ResearchRequest(topic="Topic", title="Title", key_points=["Valid", "  "])

    def test_research_request_serialization(self) -> None:
        """Verify ResearchRequest to_dict and from_dict round trip."""
        req = create_research_request(self.brief)
        data = req.to_dict()
        restored = ResearchRequest.from_dict(data)
        self.assertEqual(req, restored)


class TestResearchStorage(unittest.TestCase):
    """Test suite for research storage persistence layer."""

    def setUp(self) -> None:
        """Create temporary directory and sample ResearchPackage."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name)

        self.sample_package = ResearchPackage(
            topic="Why AI agents are becoming popular",
            sources=[
                Source(
                    title="Agent Autonomy Report",
                    url="https://example.com/agents",
                    publisher="Tech Observer",
                    retrieved_at="2026-09-04T00:00:00Z",
                )
            ],
            claims=[
                Claim(
                    statement="Agents execute multi-step tasks autonomously.",
                    status="supported",
                    evidence=[
                        Evidence(
                            source_url="https://example.com/agents",
                            excerpt="Agents successfully executed 5-step workflows.",
                            relevance="Supports autonomous execution claim.",
                        )
                    ],
                )
            ],
            summary="Verified evidence supporting agent task automation.",
        )

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_save_and_load_round_trip(self) -> None:
        """Verify saving and loading ResearchPackage produces identical data."""
        saved_path = save_research_package(
            self.sample_package, storage_dir=self.storage_dir
        )

        self.assertTrue(saved_path.is_file())
        self.assertTrue(saved_path.name.endswith(".json"))
        self.assertIn("research", saved_path.name)

        loaded = load_research_package(saved_path)
        self.assertEqual(loaded, self.sample_package)

    def test_save_collision_avoidance(self) -> None:
        """Verify consecutive saves on same topic produce distinct files."""
        path1 = save_research_package(
            self.sample_package, storage_dir=self.storage_dir
        )
        path2 = save_research_package(
            self.sample_package, storage_dir=self.storage_dir
        )

        self.assertNotEqual(path1, path2)
        self.assertTrue(path1.is_file())
        self.assertTrue(path2.is_file())

    def test_save_invalid_type_raises_storage_error(self) -> None:
        """Verify non-ResearchPackage object raises ResearchStorageError."""
        with self.assertRaises(ResearchStorageError):
            save_research_package("not a package", storage_dir=self.storage_dir)  # type: ignore

    def test_load_missing_file_raises_storage_error(self) -> None:
        """Verify attempting to load a non-existent file raises ResearchStorageError."""
        missing = self.storage_dir / "non_existent.json"
        with self.assertRaises(ResearchStorageError):
            load_research_package(missing)

    def test_slugify_helper(self) -> None:
        """Verify _slugify produces safe filenames."""
        self.assertEqual(_slugify("AI & Agents: The Future!"), "ai_agents_the_future")
        self.assertEqual(_slugify(""), "research")

    def test_default_storage_dir(self) -> None:
        """Verify default storage directory resolves to data/research."""
        d = get_default_research_storage_dir()
        self.assertTrue(str(d).endswith(str(Path("data") / "research")))


class TestResearchProviderBoundary(unittest.TestCase):
    """Test suite for research provider interface and mock implementation."""

    def test_mock_research_provider_implements_protocol(self) -> None:
        """Verify MockResearchProvider conforms to ResearchProvider protocol."""
        provider = MockResearchProvider()
        self.assertIsInstance(provider, ResearchProvider)

    def test_mock_research_provider_returns_unverified_package_without_fake_data(self) -> None:
        """Verify mock provider returns a clean package without fabricating evidence."""
        request = ResearchRequest(
            topic="Why AI agents are becoming popular",
            title="Chatbots vs AI Agents",
            key_points=["Point A", "Point B"],
        )

        provider = MockResearchProvider()
        result = provider.research(request)

        self.assertIsInstance(result, ResearchPackage)
        self.assertEqual(result.topic, request.topic)
        # Strict integrity: zero fake sources fabricated
        self.assertEqual(len(result.sources), 0)
        # Claims generated for key points default to unsupported with zero fake evidence
        self.assertEqual(len(result.claims), 2)
        for claim in result.claims:
            self.assertEqual(claim.status, "unsupported")
            self.assertEqual(len(claim.evidence), 0)

    def test_mock_research_provider_with_predefined_package(self) -> None:
        """Verify mock provider returns predefined package when supplied."""
        predefined = ResearchPackage(
            topic="Predefined Topic",
            sources=[],
            claims=[],
            summary="Predefined summary.",
        )
        provider = MockResearchProvider(predefined_package=predefined)

        request = ResearchRequest(
            topic="Different Topic",
            title="Different Title",
            key_points=["Point 1"],
        )
        result = provider.research(request)
        self.assertEqual(result, predefined)

    def test_mock_research_provider_type_errors(self) -> None:
        """Verify type checking in MockResearchProvider."""
        with self.assertRaises(TypeError):
            MockResearchProvider(predefined_package="not a package")  # type: ignore

        provider = MockResearchProvider()
        with self.assertRaises(TypeError):
            provider.research("not a request")  # type: ignore


if __name__ == "__main__":
    unittest.main()
