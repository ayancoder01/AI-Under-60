"""Unit tests for the content idea generator."""

import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.content.idea_generator import (
    IdeaGenerationError,
    _clean_json_response,
    generate_content_idea,
)
from ai_under_60.content.models import ContentIdea, ContentValidationError
from ai_under_60.main import handle_generate_idea


class TestIdeaGenerator(unittest.TestCase):
    """Test suite for AI content idea generation with mocked provider."""

    def setUp(self) -> None:
        """Standard valid JSON dictionary for mocking provider returns."""
        self.valid_response_dict = {
            "topic": "AI Coding Agents",
            "title": "Will AI Agents Replace Junior Developers?",
            "hook": "70% of code could be AI-written by 2027, but here's the catch.",
            "concept": "Explain that agents accelerate workflow but architectural reasoning still matters.",
            "target_audience": "Junior software engineers and tech enthusiasts",
            "estimated_duration_seconds": 45,
        }
        self.valid_response_json = json.dumps(self.valid_response_dict)

    def test_clean_json_response(self) -> None:
        """Verify _clean_json_response removes markdown code blocks."""
        raw_markdown = f"```json\n{self.valid_response_json}\n```"
        cleaned = _clean_json_response(raw_markdown)
        self.assertEqual(cleaned, self.valid_response_json)

        raw_plain = f"```\n{self.valid_response_json}\n```"
        self.assertEqual(_clean_json_response(raw_plain), self.valid_response_json)

        self.assertEqual(_clean_json_response(self.valid_response_json), self.valid_response_json)

    def test_empty_topic_raises_value_error(self) -> None:
        """Verify empty topic string raises ValueError."""
        with self.assertRaises(ValueError):
            generate_content_idea("")

        with self.assertRaises(ValueError):
            generate_content_idea("   \n\t  ")

    def test_generate_content_idea_success(self) -> None:
        """Verify successful generation and parsing with mocked provider."""
        mock_provider = MagicMock(return_value=self.valid_response_json)

        idea = generate_content_idea("AI Coding Agents", provider=mock_provider)

        self.assertIsInstance(idea, ContentIdea)
        self.assertEqual(idea.topic, "AI Coding Agents")
        self.assertEqual(idea.title, "Will AI Agents Replace Junior Developers?")
        self.assertEqual(idea.estimated_duration_seconds, 45)
        mock_provider.assert_called_once()
        self.assertIn("AI Coding Agents", mock_provider.call_args[0][0])

    def test_generate_content_idea_with_markdown_wrapper(self) -> None:
        """Verify markdown code blocks returned by AI are stripped cleanly."""
        markdown_wrapped = f"```json\n{self.valid_response_json}\n```"
        mock_provider = MagicMock(return_value=markdown_wrapped)

        idea = generate_content_idea("AI Coding Agents", provider=mock_provider)
        self.assertEqual(idea.title, "Will AI Agents Replace Junior Developers?")

    def test_provider_failure_raises_idea_generation_error(self) -> None:
        """Verify provider exceptions are wrapped in IdeaGenerationError."""
        mock_provider = MagicMock(side_effect=RuntimeError("Provider network timeout"))

        with self.assertRaises(IdeaGenerationError) as ctx:
            generate_content_idea("Any Topic", provider=mock_provider)

        self.assertIn("Content idea generation failed", str(ctx.exception))

    def test_malformed_json_raises_idea_generation_error(self) -> None:
        """Verify malformed JSON from provider raises IdeaGenerationError."""
        mock_provider = MagicMock(return_value="This is definitely not JSON at all.")

        with self.assertRaises(IdeaGenerationError) as ctx:
            generate_content_idea("Any Topic", provider=mock_provider)

        self.assertIn("malformed JSON", str(ctx.exception))

    def test_non_dict_json_raises_idea_generation_error(self) -> None:
        """Verify JSON array or scalar response raises IdeaGenerationError."""
        mock_provider = MagicMock(return_value='["topic 1", "topic 2"]')

        with self.assertRaises(IdeaGenerationError) as ctx:
            generate_content_idea("Any Topic", provider=mock_provider)

        self.assertIn("Expected JSON object", str(ctx.exception))

    def test_missing_fields_raises_content_validation_error(self) -> None:
        """Verify missing required JSON fields raise ContentValidationError."""
        incomplete_dict = {"topic": "AI", "title": "Just a Title"}
        mock_provider = MagicMock(return_value=json.dumps(incomplete_dict))

        with self.assertRaises(ContentValidationError):
            generate_content_idea("AI", provider=mock_provider)

    def test_invalid_duration_raises_content_validation_error(self) -> None:
        """Verify duration > 60 raises ContentValidationError."""
        invalid_dict = self.valid_response_dict.copy()
        invalid_dict["estimated_duration_seconds"] = 90
        mock_provider = MagicMock(return_value=json.dumps(invalid_dict))

        with self.assertRaises(ContentValidationError):
            generate_content_idea("AI Coding Agents", provider=mock_provider)

    def test_handle_generate_idea_cli_empty_topic(self) -> None:
        """Verify handle_generate_idea exits with 1 when topic is empty."""
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            exit_code = handle_generate_idea("")

        self.assertEqual(exit_code, 1)
        self.assertIn("[ERROR]", captured.getvalue())

    def test_handle_generate_idea_cli_success(self) -> None:
        """Verify handle_generate_idea succeeds and prints structured output."""
        mock_idea = ContentIdea(**self.valid_response_dict)
        mock_path = Path("/mock/data/content_ideas/idea.json")

        with patch("ai_under_60.content.generate_content_idea", return_value=mock_idea), \
             patch("ai_under_60.content.save_content_idea", return_value=mock_path):
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                exit_code = handle_generate_idea("AI Coding Agents")

            self.assertEqual(exit_code, 0)
            output = captured.getvalue()
            self.assertIn("Will AI Agents Replace Junior Developers?", output)
            self.assertIn("Estimated Duration:         45s", output)
            self.assertIn(str(mock_path), output)


if __name__ == "__main__":
    unittest.main()
