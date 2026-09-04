"""Unit tests for the live web research provider (mocked boundary, 100% offline)."""

import io
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.main import handle_research, main
from ai_under_60.research.models import Claim, Evidence, ResearchPackage, Source
from ai_under_60.research.request import ResearchRequest
from ai_under_60.research.web import (
    WebResearchProvider,
    _looks_like_noise,
    classify_source_quality,
    extract_publisher,
    extract_text_from_html,
    find_evidence_in_text,
    generate_search_queries,
    normalize_url,
)


class TestWebResearchHelpers(unittest.TestCase):
    """Test suite for URL normalization, publisher extraction, text parsing, and query generation."""

    def test_normalize_url(self) -> None:
        """Verify normalize_url cleans URLs, strips fragments, and unquotes DDG wrappers."""
        # Standard clean URL
        self.assertEqual(
            normalize_url("https://example.com/path/to/page#section"),
            "https://example.com/path/to/page",
        )

        # DDG redirect wrapper
        ddg_wrapped = (
            "//duckduckgo.com/l/?uddg=https%3A%2F%2Fforbes.com%2Farticle%2Fagents&rut=123"
        )
        self.assertEqual(
            normalize_url(ddg_wrapped),
            "https://forbes.com/article/agents",
        )

        # Trailing slash normalization
        self.assertEqual(
            normalize_url("https://example.com/dir/"),
            "https://example.com/dir",
        )

        # Invalid schemes or malformed URLs
        self.assertEqual(normalize_url("javascript:alert(1)"), "")
        self.assertEqual(normalize_url("ftp://example.com/file"), "")
        self.assertEqual(normalize_url(""), "")
        self.assertEqual(normalize_url("not a url"), "")

    def test_extract_publisher(self) -> None:
        """Verify publisher derivation from URL netloc."""
        self.assertEqual(extract_publisher("https://www.forbes.com/article"), "forbes.com")
        self.assertEqual(extract_publisher("https://blog.praxisforge.com/post"), "blog.praxisforge.com")
        self.assertEqual(extract_publisher("invalid url"), "Web Source")

    def test_generate_search_queries(self) -> None:
        """Verify query generation from topic, title, and key points."""
        request = ResearchRequest(
            topic="Why AI agents are becoming popular",
            title="Why Chatbots Are DEAD (Meet AI Agents)",
            key_points=[
                "AI agents automate complex multi-step workflows autonomously",
                "Companies invest billions into autonomous agent infrastructure",
            ],
        )

        queries = generate_search_queries(request, max_queries=4)
        self.assertGreaterEqual(len(queries), 2)
        self.assertLessEqual(len(queries), 4)

        # First query should be the primary topic
        self.assertEqual(queries[0], "Why AI agents are becoming popular")
        # Ensure no duplicates
        self.assertEqual(len(queries), len(set(q.lower() for q in queries)))

    def test_extract_text_from_html(self) -> None:
        """Verify HTML tag stripping, script/style removal, and entity decoding."""
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <style>body { color: red; }</style>
            <script>console.log('tracker');</script>
        </head>
        <body>
            <!-- Navigation header should be removed -->
            <nav><a href="/">Home</a> <a href="/about">About</a></nav>
            <header>Site Header</header>

            <main>
                <h1>AI Agents in 2026</h1>
                <p>Autonomous AI agents are transforming enterprise operations &amp; productivity.</p>
                <p>They execute multi-step workflows without manual intervention.</p>
            </main>

            <footer>Copyright &copy; 2026</footer>
        </body>
        </html>
        """

        clean_text = extract_text_from_html(sample_html)
        self.assertNotIn("console.log", clean_text)
        self.assertNotIn("color: red", clean_text)
        self.assertNotIn("Site Header", clean_text)
        self.assertNotIn("Copyright", clean_text)
        self.assertIn("AI Agents in 2026", clean_text)
        self.assertIn("Autonomous AI agents are transforming enterprise operations & productivity.", clean_text)
        self.assertIn("They execute multi-step workflows without manual intervention.", clean_text)

    def test_find_evidence_in_text(self) -> None:
        """Verify find_evidence_in_text extracts factual excerpts matching statement keywords."""
        text = (
            "The market for software automation is shifting rapidly. "
            "Autonomous AI agents are executing multi-step business workflows without human intervention. "
            "Enterprise adoption increased by over 300 percent in the last twelve months. "
            "Weather forecasts predict rain tomorrow."
        )
        url = "https://example.com/report"
        statement = "Autonomous AI agents execute business workflows without human intervention."

        evidence = find_evidence_in_text(
            text=text,
            source_url=url,
            statement=statement,
            min_keyword_matches=2,
        )

        self.assertGreaterEqual(len(evidence), 1)
        self.assertEqual(evidence[0].source_url, url)
        self.assertIn("Autonomous AI agents are executing multi-step business workflows", evidence[0].excerpt)
        self.assertIn("Excerpt contains key terms", evidence[0].relevance)

    def test_find_evidence_no_match(self) -> None:
        """Verify find_evidence_in_text returns empty list when no sentences match statement."""
        text = "Just discussing baking chocolate chip cookies with organic flour and sugar."
        url = "https://example.com/cookies"
        statement = "Quantum computing breaks 2048-bit RSA encryption."

        evidence = find_evidence_in_text(
            text=text,
            source_url=url,
            statement=statement,
            min_keyword_matches=2,
        )
        self.assertEqual(len(evidence), 0)


class TestWebResearchProviderOffline(unittest.TestCase):
    """Test suite for WebResearchProvider with mocked HTTP/search boundaries."""

    def setUp(self) -> None:
        """Prepare sample ResearchRequest."""
        self.request = ResearchRequest(
            topic="Why AI agents are becoming popular",
            title="Chatbots vs AI Agents",
            key_points=[
                "AI agents execute multi-step workflows autonomously",
                "Companies invest billions into agent technology",
            ],
        )

    def test_provider_success_with_evidence(self) -> None:
        """Verify provider coordinates search, page fetching, and evidence extraction."""
        mock_search_results = [
            {
                "title": "The Rise of AI Agents",
                "url": "https://techjournal.com/ai-agents-rise",
                "snippet": "Analysis of autonomous AI agent adoption.",
                "publisher": "techjournal.com",
            },
            {
                "title": "Enterprise Automation in 2026",
                "url": "https://industrynews.org/enterprise-automation",
                "snippet": "How companies invest billions in autonomous workflows.",
                "publisher": "industrynews.org",
            },
        ]

        def mock_search_fn(query: str, timeout: int) -> list:
            return mock_search_results

        def mock_page_fetcher(url: str, timeout: int) -> str:
            if "techjournal.com" in url:
                return (
                    "Modern technology report. AI agents execute multi-step workflows autonomously "
                    "across various industries with minimal error rates."
                )
            return (
                "Financial briefing. Global companies invest billions into agent technology "
                "to automate internal processes and customer service."
            )

        provider = WebResearchProvider(
            search_fn=mock_search_fn,
            page_fetcher=mock_page_fetcher,
            max_queries=2,
            max_sources=2,
        )

        package = provider.research(self.request)

        self.assertIsInstance(package, ResearchPackage)
        self.assertEqual(package.topic, self.request.topic)
        self.assertEqual(len(package.sources), 2)
        self.assertEqual(package.sources[0].url, "https://techjournal.com/ai-agents-rise")
        self.assertEqual(package.sources[1].url, "https://industrynews.org/enterprise-automation")

        # Verify claims have real evidence
        self.assertEqual(len(package.claims), 2)
        for claim in package.claims:
            self.assertIn(claim.status, ("supported", "uncertain"))
            self.assertGreaterEqual(len(claim.evidence), 1)
            # Verify evidence points to real source URLs
            for ev in claim.evidence:
                self.assertIn(ev.source_url, [s.url for s in package.sources])

        # Verify summary contains source count
        self.assertIn("2 web sources", package.summary)
        self.assertNotIn("verified web sources", package.summary)

    def test_provider_unsupported_claims_when_no_evidence_matches(self) -> None:
        """Verify claims remain unsupported with empty evidence when pages do not substantiate them."""
        mock_search_results = [
            {
                "title": "Irrelevant Topic",
                "url": "https://example.com/unrelated",
                "snippet": "Discussion about gardening and greenhouse vegetables.",
                "publisher": "example.com",
            }
        ]

        def mock_search_fn(query: str, timeout: int) -> list:
            return mock_search_results

        def mock_page_fetcher(url: str, timeout: int) -> str:
            return "Gardening tips for growing tomatoes and cucumbers in raised garden beds."

        provider = WebResearchProvider(
            search_fn=mock_search_fn,
            page_fetcher=mock_page_fetcher,
        )

        package = provider.research(self.request)

        self.assertEqual(len(package.sources), 1)
        self.assertEqual(len(package.claims), 2)
        # All claims must be marked unsupported because no evidence exists
        for claim in package.claims:
            self.assertEqual(claim.status, "unsupported")
            self.assertEqual(len(claim.evidence), 0)

    def test_provider_handles_empty_search_results(self) -> None:
        """Verify provider produces honest ResearchPackage when search returns zero results."""
        def mock_empty_search(query: str, timeout: int) -> list:
            return []

        provider = WebResearchProvider(search_fn=mock_empty_search)
        package = provider.research(self.request)

        self.assertEqual(len(package.sources), 0)
        self.assertEqual(len(package.claims), 2)
        for claim in package.claims:
            self.assertEqual(claim.status, "unsupported")
            self.assertEqual(len(claim.evidence), 0)
        self.assertIn("yielded no accessible web sources", package.summary)

    def test_provider_handles_search_exception_gracefully(self) -> None:
        """Verify search exceptions do not crash the research run."""
        def mock_failing_search(query: str, timeout: int) -> list:
            raise ConnectionError("Network unreachable")

        provider = WebResearchProvider(search_fn=mock_failing_search)
        package = provider.research(self.request)

        self.assertEqual(len(package.sources), 0)
        self.assertEqual(len(package.claims), 2)
        self.assertIn("yielded no accessible web sources", package.summary)

    def test_provider_handles_page_fetch_errors_gracefully(self) -> None:
        """Verify individual page fetch errors do not abort other sources."""
        mock_results = [
            {
                "title": "Failing Page",
                "url": "https://failing.com/404",
                "snippet": "",
                "publisher": "failing.com",
            },
            {
                "title": "Working Page",
                "url": "https://working.com/good",
                "snippet": "Good snippet",
                "publisher": "working.com",
            },
        ]

        def mock_search_fn(query: str, timeout: int) -> list:
            return mock_results

        def mock_page_fetcher(url: str, timeout: int) -> str | None:
            if "failing.com" in url:
                raise TimeoutError("Page timed out")
            return "Working page content discussing AI agents and automation technology."

        provider = WebResearchProvider(
            search_fn=mock_search_fn,
            page_fetcher=mock_page_fetcher,
        )

        package = provider.research(self.request)
        # Should retain the working source
        self.assertEqual(len(package.sources), 1)
        self.assertEqual(package.sources[0].url, "https://working.com/good")

    def test_provider_deduplicates_sources(self) -> None:
        """Verify duplicate URLs across queries are fetched only once."""
        mock_results = [
            {
                "title": "Duplicated Article",
                "url": "https://example.com/duplicate/",
                "snippet": "Article snippet",
                "publisher": "example.com",
            },
            {
                "title": "Duplicated Article Again",
                "url": "https://example.com/duplicate#section2",
                "snippet": "Same article snippet",
                "publisher": "example.com",
            },
        ]

        fetch_count = 0

        def mock_search_fn(query: str, timeout: int) -> list:
            return mock_results

        def mock_page_fetcher(url: str, timeout: int) -> str:
            nonlocal fetch_count
            fetch_count += 1
            return "Valid article body with content about AI agents and autonomy."

        provider = WebResearchProvider(
            search_fn=mock_search_fn,
            page_fetcher=mock_page_fetcher,
        )

        package = provider.research(self.request)
        # Normalized URLs are identical ("https://example.com/duplicate")
        self.assertEqual(len(package.sources), 1)
        self.assertEqual(fetch_count, 1)

    def test_provider_type_error_on_invalid_request(self) -> None:
        """Verify passing non-ResearchRequest raises TypeError."""
        provider = WebResearchProvider()
        with self.assertRaises(TypeError):
            provider.research("not a request")  # type: ignore


class TestResearchCLI(unittest.TestCase):
    """Test suite for the --research CLI command."""

    def test_handle_research_success(self) -> None:
        """Verify handle_research executes and outputs formatted summary and saved path."""
        sample_package = ResearchPackage(
            topic="Why AI agents are becoming popular",
            sources=[
                Source(
                    title="Real Source Title",
                    url="https://example.com/agents",
                    publisher="example.com",
                    retrieved_at="2026-09-04T00:00:00Z",
                )
            ],
            claims=[
                Claim(
                    statement="Agents automate tasks.",
                    status="supported",
                    evidence=[
                        Evidence(
                            source_url="https://example.com/agents",
                            excerpt="Agents automate tasks efficiently.",
                            relevance="Direct evidence",
                        )
                    ],
                )
            ],
            summary="Research summary of AI agents.",
        )

        mock_saved_path = Path("/mock/research.json")
        with patch("ai_under_60.research.web.WebResearchProvider.research", return_value=sample_package):
            with patch("ai_under_60.research.save_research_package", return_value=mock_saved_path):
                captured = io.StringIO()
                with patch("sys.stdout", captured):
                    code = handle_research("Why AI agents are becoming popular")

                self.assertEqual(code, 0)
                out = captured.getvalue()
                self.assertIn("AI Under 60 - Web Research Engine", out)
                self.assertIn("Research Summary:", out)
                self.assertIn("Sources Retrieved:  1", out)
                self.assertIn("Real Source Title", out)
                self.assertIn("[SUPPORTED] Agents automate tasks.", out)
                self.assertIn(str(mock_saved_path), out)


    def test_handle_research_empty_topic(self) -> None:
        """Verify handle_research returns 1 on empty topic."""
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = handle_research("")

        self.assertEqual(code, 1)
        self.assertIn("[ERROR]", captured.getvalue())

    def test_handle_research_exception_handling(self) -> None:
        """Verify handle_research catches exceptions and returns error code 1."""
        with patch(
            "ai_under_60.research.web.WebResearchProvider.research",
            side_effect=RuntimeError("Research execution error"),
        ):
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                code = handle_research("Valid Topic")

            self.assertEqual(code, 1)
            self.assertIn("Web research failed: Research execution error", captured.getvalue())

    def test_main_cli_research_routing(self) -> None:
        """Verify main() routes --research to handle_research."""
        with patch.object(sys, "argv", ["main.py", "--research", "Test Topic"]):
            with patch("ai_under_60.main.handle_research", return_value=0) as mock_handle:
                code = main()
                self.assertEqual(code, 0)
                mock_handle.assert_called_once_with("Test Topic")



class TestClassifySourceQuality(unittest.TestCase):
    """Test suite for the classify_source_quality domain-classification function."""

    def test_reputable_secondary_exact_match(self) -> None:
        """Known reputable domains return reputable_secondary."""
        self.assertEqual(classify_source_quality("https://time.com/article"), "reputable_secondary")
        self.assertEqual(classify_source_quality("https://www.reuters.com/tech"), "reputable_secondary")
        self.assertEqual(classify_source_quality("https://techcrunch.com/ai"), "reputable_secondary")
        self.assertEqual(classify_source_quality("https://www.bbc.com/news"), "reputable_secondary")
        self.assertEqual(classify_source_quality("https://mit.edu/research"), "reputable_secondary")

    def test_reputable_secondary_subdomain_match(self) -> None:
        """Subdomains of reputable domains also classify as reputable_secondary."""
        self.assertEqual(classify_source_quality("https://news.mit.edu/story"), "reputable_secondary")
        self.assertEqual(classify_source_quality("https://blog.wired.com/post"), "reputable_secondary")

    def test_user_generated_domains(self) -> None:
        """Known social/UGC domains return user_generated."""
        self.assertEqual(classify_source_quality("https://linkedin.com/posts/ai"), "user_generated")
        self.assertEqual(classify_source_quality("https://www.reddit.com/r/MachineLearning"), "user_generated")
        self.assertEqual(classify_source_quality("https://medium.com/@author/story"), "user_generated")
        self.assertEqual(classify_source_quality("https://twitter.com/user"), "user_generated")

    def test_general_secondary_unknown_domains(self) -> None:
        """Unknown domains return general_secondary."""
        self.assertEqual(classify_source_quality("https://aitoolinsight.com/article"), "general_secondary")
        self.assertEqual(classify_source_quality("https://someblog.example.com/post"), "general_secondary")
        self.assertEqual(classify_source_quality("https://newsite12345.net/article"), "general_secondary")

    def test_unknown_for_unparseable_inputs(self) -> None:
        """Empty or non-URL inputs return unknown."""
        self.assertEqual(classify_source_quality(""), "unknown")
        self.assertEqual(classify_source_quality("   "), "unknown")
        self.assertEqual(classify_source_quality("not-a-url"), "unknown")

    def test_source_quality_stored_on_source_model(self) -> None:
        """Source dataclass accepts and stores source_quality correctly."""
        from ai_under_60.research.models import Source
        source = Source(
            title="Test Article",
            url="https://time.com/article",
            publisher="time.com",
            retrieved_at="2026-09-04T00:00:00Z",
            source_quality="reputable_secondary",
        )
        self.assertEqual(source.source_quality, "reputable_secondary")
        d = source.to_dict()
        self.assertIn("source_quality", d)
        self.assertEqual(d["source_quality"], "reputable_secondary")

    def test_source_from_dict_backward_compat_missing_quality(self) -> None:
        """Source.from_dict without source_quality key defaults to unknown."""
        from ai_under_60.research.models import Source
        data = {
            "title": "Old Article",
            "url": "https://example.com/old",
            "publisher": "example.com",
            "retrieved_at": "2026-09-04T00:00:00Z",
        }
        source = Source.from_dict(data)
        self.assertEqual(source.source_quality, "unknown")

    def test_source_quality_invalid_value_raises(self) -> None:
        """Source raises ResearchValidationError for unknown source_quality value."""
        from ai_under_60.research.models import ResearchValidationError, Source
        with self.assertRaises(ResearchValidationError):
            Source(
                title="Test",
                url="https://example.com",
                publisher="example.com",
                retrieved_at="2026-09-04T00:00:00Z",
                source_quality="garbage_tier",
            )


class TestLooksLikeNoise(unittest.TestCase):
    """Unit tests for the _looks_like_noise heuristic."""

    def test_genuine_prose_is_not_noise(self) -> None:
        """Normal article prose should NOT be flagged as noise."""
        self.assertFalse(_looks_like_noise(
            "Autonomous AI agents are transforming enterprise workflows by executing "
            "multi-step tasks without manual intervention."
        ))
        self.assertFalse(_looks_like_noise(
            "Companies worldwide invested over three hundred billion dollars in AI "
            "infrastructure and research during the past two years."
        ))

    def test_linkedin_feed_artifact_is_noise(self) -> None:
        """LinkedIn-style feed lines with numeric timestamps should be flagged."""
        # e.g. "1y 9 AI Tools I Use to Run a Growth System in 2026 Jake Lee"
        self.assertTrue(_looks_like_noise(
            "1y 9 AI Tools I Use to Run a Growth System in 2026 Jake Lee"
        ))

    def test_high_numeric_density_is_noise(self) -> None:
        """Sentences dominated by numeric tokens are flagged as noise."""
        self.assertTrue(_looks_like_noise("1 2 3 4 5 6 7 8 9 10 11 12 13 14 15"))

    def test_short_abbreviation_heavy_sentence_is_noise(self) -> None:
        """Sentences with many digit+letter abbreviations are flagged."""
        self.assertTrue(_looks_like_noise("1y 2h 3d 4w Read AI Tools Growth Systems"))


class TestEvidenceNoiseRegression(unittest.TestCase):
    """Regression test: sidebar/feed noise must NOT appear as evidence.

    This test constructs HTML with:
    (a) A genuine article paragraph about AI agents (should be extracted).
    (b) A sidebar recommendation feed mimicking LinkedIn-style output (must be rejected).

    Verifies that find_evidence_in_text returns only the genuine article evidence.
    """

    ARTICLE_HTML = """
    <html>
    <body>
    <nav>Home About Contact</nav>
    <header>AI Research Daily</header>
    <main>
        <article>
            <h1>Why AI Agents Are Transforming Business</h1>
            <p>Autonomous AI agents are executing complex multi-step business workflows
            without requiring human intervention at each stage. Enterprise adoption has
            increased significantly as companies invest in agent-based automation.</p>
            <p>Traditional software could only respond to explicit commands. Modern AI agents
            autonomously plan, reason, and execute sequences of tasks across different systems.</p>
        </article>
    </main>
    <aside>
        <ul>
            <li>1y 9 AI Tools I Use to Run a Growth System in 2026 Jake Lee</li>
            <li>2h AI agents trending now follow for updates</li>
            <li>3d Why Chatbots Are DEAD Meet AI Agents John Smith</li>
        </ul>
    </aside>
    <footer>Copyright 2026 AI Research Daily</footer>
    </body>
    </html>
    """

    def test_sidebar_noise_not_returned_as_evidence(self) -> None:
        """Feed/sidebar text is rejected and does not appear in evidence excerpts."""
        text = extract_text_from_html(self.ARTICLE_HTML)
        statement = "Autonomous AI agents execute complex business workflows without human intervention."
        url = "https://airesearchdaily.com/article"

        evidence = find_evidence_in_text(
            text=text,
            source_url=url,
            statement=statement,
            min_keyword_matches=2,
        )

        # Verify the noisy feed lines are NOT in any evidence excerpt
        for ev in evidence:
            self.assertNotIn("1y", ev.excerpt, "Feed artifact '1y' leaked into evidence")
            self.assertNotIn("Jake Lee", ev.excerpt, "Feed author name leaked into evidence")
            self.assertNotIn("2h", ev.excerpt, "Feed timestamp '2h' leaked into evidence")

    def test_genuine_article_text_still_extracted(self) -> None:
        """Genuine article sentences that match the statement are still returned."""
        text = extract_text_from_html(self.ARTICLE_HTML)
        statement = "Autonomous AI agents execute complex business workflows without human intervention."
        url = "https://airesearchdaily.com/article"

        evidence = find_evidence_in_text(
            text=text,
            source_url=url,
            statement=statement,
            min_keyword_matches=2,
        )

        # At least one evidence excerpt should come from the genuine article paragraph
        self.assertGreaterEqual(
            len(evidence), 1,
            "Expected at least one genuine evidence excerpt from article body."
        )
        # The genuine excerpt should contain meaningful article content
        genuine_terms = {"agents", "autonomous", "workflows", "business", "intervention"}
        found_genuine = any(
            any(term in ev.excerpt.lower() for term in genuine_terms)
            for ev in evidence
        )
        self.assertTrue(found_genuine, "No evidence excerpt contained expected article terms.")


if __name__ == "__main__":
    unittest.main()
