"""Unit tests for the content generation pipeline and CLI integration."""

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.content.models import (
    ContentBrief,
    ContentIdea,
    ContentValidationError,
)
from ai_under_60.content.pipeline import (
    PipelineError,
    PipelineResult,
    run_content_pipeline,
)
from ai_under_60.content.storage import StorageError
from ai_under_60.main import handle_generate_content, main


class TestContentPipeline(unittest.TestCase):
    """Test suite for the end-to-end content generation pipeline."""

    def setUp(self) -> None:
        """Set up standard valid idea/brief fixtures and temporary storage dirs."""
        self.valid_topic = "Why AI agents are becoming popular"
        self.valid_idea_dict = {
            "topic": self.valid_topic,
            "title": "Why Chatbots Are DEAD (Meet AI Agents)",
            "hook": "Stop asking ChatGPT questions—that's already outdated.",
            "concept": "Visual Beat 1: Chatbots only chat. Visual Beat 2: AI agents book flights and execute code. Final Beat: The future is autonomous.",
            "target_audience": "Tech enthusiasts and developers",
            "estimated_duration_seconds": 45,
        }
        self.valid_idea_json = json.dumps(self.valid_idea_dict)

        self.temp_dir = tempfile.TemporaryDirectory()
        self.ideas_dir = Path(self.temp_dir.name) / "content_ideas"
        self.briefs_dir = Path(self.temp_dir.name) / "content_briefs"

    def tearDown(self) -> None:
        """Clean up temporary directories."""
        self.temp_dir.cleanup()

    # ------------------------------------------------------------------
    # Input validation tests
    # ------------------------------------------------------------------

    def test_empty_topic_raises_value_error(self) -> None:
        """Verify empty topic string raises ValueError."""
        with self.assertRaises(ValueError):
            run_content_pipeline("")

        with self.assertRaises(ValueError):
            run_content_pipeline("   \n\t  ")

        with self.assertRaises(ValueError):
            run_content_pipeline(None)  # type: ignore

    # ------------------------------------------------------------------
    # Successful pipeline execution tests
    # ------------------------------------------------------------------

    def test_pipeline_success_with_mock_provider(self) -> None:
        """Verify pipeline successfully executes all steps and returns artifacts."""
        mock_provider = MagicMock(return_value=self.valid_idea_json)

        result = run_content_pipeline(
            self.valid_topic,
            provider=mock_provider,
            ideas_storage_dir=self.ideas_dir,
            briefs_storage_dir=self.briefs_dir,
        )

        # Verify returned result structure
        self.assertIsInstance(result, PipelineResult)
        self.assertIsInstance(result.idea, ContentIdea)
        self.assertIsInstance(result.brief, ContentBrief)

        # Verify idea contents
        self.assertEqual(result.idea.topic, self.valid_topic)
        self.assertEqual(result.idea.title, self.valid_idea_dict["title"])

        # Verify brief contents
        self.assertEqual(result.brief.topic, self.valid_topic)
        self.assertEqual(result.brief.title, self.valid_idea_dict["title"])
        self.assertGreaterEqual(len(result.brief.key_points), 1)

        # Verify persistence
        self.assertTrue(result.idea_path.is_file())
        self.assertTrue(result.brief_path.is_file())
        self.assertEqual(result.idea_path.parent, self.ideas_dir)
        self.assertEqual(result.brief_path.parent, self.briefs_dir)

        # Verify dictionary representation
        result_dict = result.to_dict()
        self.assertIn("idea", result_dict)
        self.assertIn("brief", result_dict)
        self.assertEqual(result_dict["idea_path"], str(result.idea_path))
        self.assertEqual(result_dict["brief_path"], str(result.brief_path))

    # ------------------------------------------------------------------
    # Failure handling tests
    # ------------------------------------------------------------------

    def test_pipeline_failure_when_idea_generation_fails(self) -> None:
        """Verify provider errors during idea generation raise PipelineError."""
        mock_provider = MagicMock(side_effect=RuntimeError("AI provider unreachable"))

        with self.assertRaises(PipelineError) as ctx:
            run_content_pipeline(
                self.valid_topic,
                provider=mock_provider,
                ideas_storage_dir=self.ideas_dir,
                briefs_storage_dir=self.briefs_dir,
            )

        self.assertIn("Content idea generation failed", str(ctx.exception))

    def test_pipeline_failure_when_idea_validation_fails(self) -> None:
        """Verify invalid generated ContentIdea raises PipelineError."""
        invalid_idea_dict = self.valid_idea_dict.copy()
        invalid_idea_dict["estimated_duration_seconds"] = 99  # Exceeds 60s max
        mock_provider = MagicMock(return_value=json.dumps(invalid_idea_dict))

        with self.assertRaises(PipelineError) as ctx:
            run_content_pipeline(
                self.valid_topic,
                provider=mock_provider,
                ideas_storage_dir=self.ideas_dir,
                briefs_storage_dir=self.briefs_dir,
            )

        self.assertIn("Content idea validation failed", str(ctx.exception))

    def test_pipeline_failure_when_brief_conversion_fails(self) -> None:
        """Verify errors during brief conversion raise PipelineError."""
        mock_provider = MagicMock(return_value=self.valid_idea_json)

        with patch(
            "ai_under_60.content.pipeline.content_idea_to_brief",
            side_effect=RuntimeError("Conversion error"),
        ):
            with self.assertRaises(PipelineError) as ctx:
                run_content_pipeline(
                    self.valid_topic,
                    provider=mock_provider,
                    ideas_storage_dir=self.ideas_dir,
                    briefs_storage_dir=self.briefs_dir,
                )

            self.assertIn("Content brief conversion failed", str(ctx.exception))

    def test_pipeline_failure_when_brief_validation_fails(self) -> None:
        """Verify validation errors during brief conversion raise PipelineError."""
        mock_provider = MagicMock(return_value=self.valid_idea_json)

        with patch(
            "ai_under_60.content.pipeline.content_idea_to_brief",
            side_effect=ContentValidationError("Invalid key points"),
        ):
            with self.assertRaises(PipelineError) as ctx:
                run_content_pipeline(
                    self.valid_topic,
                    provider=mock_provider,
                    ideas_storage_dir=self.ideas_dir,
                    briefs_storage_dir=self.briefs_dir,
                )

            self.assertIn("Content brief validation failed", str(ctx.exception))

    def test_pipeline_failure_when_idea_persistence_fails(self) -> None:
        """Verify persistence errors for ContentIdea raise PipelineError."""
        mock_provider = MagicMock(return_value=self.valid_idea_json)

        with patch(
            "ai_under_60.content.pipeline.save_content_idea",
            side_effect=StorageError("Disk write error"),
        ):
            with self.assertRaises(PipelineError) as ctx:
                run_content_pipeline(
                    self.valid_topic,
                    provider=mock_provider,
                    ideas_storage_dir=self.ideas_dir,
                    briefs_storage_dir=self.briefs_dir,
                )

            self.assertIn("Failed to persist content idea", str(ctx.exception))

    def test_pipeline_failure_when_brief_persistence_fails(self) -> None:
        """Verify persistence errors for ContentBrief raise PipelineError."""
        mock_provider = MagicMock(return_value=self.valid_idea_json)

        with patch(
            "ai_under_60.content.pipeline.save_content_brief",
            side_effect=StorageError("Directory unwritable"),
        ):
            with self.assertRaises(PipelineError) as ctx:
                run_content_pipeline(
                    self.valid_topic,
                    provider=mock_provider,
                    ideas_storage_dir=self.ideas_dir,
                    briefs_storage_dir=self.briefs_dir,
                )

            self.assertIn("Failed to persist content brief", str(ctx.exception))

    # ------------------------------------------------------------------
    # CLI handler tests
    # ------------------------------------------------------------------

    def test_handle_generate_content_cli_success(self) -> None:
        """Verify CLI handler executes pipeline and outputs all expected sections."""
        sample_idea = ContentIdea(**self.valid_idea_dict)
        sample_brief = ContentBrief(
            topic=sample_idea.topic,
            title=sample_idea.title,
            hook=sample_idea.hook,
            concept=sample_idea.concept,
            target_audience=sample_idea.target_audience,
            estimated_duration_seconds=sample_idea.estimated_duration_seconds,
            key_points=["Point 1", "Point 2"],
            call_to_action="Follow @AIUnder60!",
        )
        mock_result = PipelineResult(
            idea=sample_idea,
            brief=sample_brief,
            idea_path=Path("/mock/ideas/idea.json"),
            brief_path=Path("/mock/briefs/brief.json"),
        )

        with patch("ai_under_60.content.run_content_pipeline", return_value=mock_result):
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                code = handle_generate_content(self.valid_topic)

            self.assertEqual(code, 0)
            output = captured.getvalue()
            self.assertIn("AI Under 60 - Content Generation Pipeline", output)
            self.assertIn(self.valid_idea_dict["title"], output)
            self.assertIn(self.valid_idea_dict["hook"], output)
            self.assertIn("ContentIdea Saved to:", output)
            self.assertIn("ContentBrief Saved to:", output)
            self.assertIn(str(mock_result.idea_path), output)
            self.assertIn(str(mock_result.brief_path), output)


    def test_handle_generate_content_cli_empty_topic(self) -> None:
        """Verify CLI handler returns error code 1 on empty topic."""
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = handle_generate_content("")

        self.assertEqual(code, 1)
        self.assertIn("[ERROR]", captured.getvalue())

    def test_handle_generate_content_cli_pipeline_error(self) -> None:
        """Verify CLI handler catches PipelineError and returns error code 1."""
        with patch(
            "ai_under_60.content.run_content_pipeline",
            side_effect=PipelineError("Pipeline step failed"),
        ):
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                code = handle_generate_content(self.valid_topic)

            self.assertEqual(code, 1)
            self.assertIn("Pipeline step failed", captured.getvalue())

    def test_main_cli_generate_content_routing(self) -> None:
        """Verify main() routes --generate-content to handle_generate_content."""
        with patch.object(
            sys, "argv", ["main.py", "--generate-content", "My Topic"]
        ):
            with patch(
                "ai_under_60.main.handle_generate_content", return_value=0
            ) as mock_handler:
                code = main()
                self.assertEqual(code, 0)
                mock_handler.assert_called_once_with("My Topic")


if __name__ == "__main__":
    unittest.main()
