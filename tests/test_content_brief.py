"""Unit tests for ContentBrief model, conversion, storage, and CLI handler."""

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

from ai_under_60.content.brief import (
    DEFAULT_CALL_TO_ACTION,
    content_idea_to_brief,
    extract_key_points_from_concept,
)
from ai_under_60.content.models import (
    ContentBrief,
    ContentIdea,
    ContentValidationError,
)
from ai_under_60.content.storage import (
    StorageError,
    load_content_brief,
    save_content_brief,
)
from ai_under_60.main import handle_brief_from_idea, main


class TestContentBrief(unittest.TestCase):
    """Test suite for ContentBrief model, conversion, storage, and CLI."""

    def setUp(self) -> None:
        """Set up standard valid test fixtures."""
        self.valid_brief_data = {
            "topic": "Why AI agents are becoming popular",
            "title": "Why Chatbots Are DEAD (Meet AI Agents)",
            "hook": "Stop asking ChatGPT questions—that's already outdated.",
            "concept": "Fast-paced split-screen video contrasting passive AI with active AI. Visual Beat 1: Left shows chatbot. Visual Beat 2: Right shows agent booking flights.",
            "target_audience": "Tech enthusiasts and developers",
            "estimated_duration_seconds": 45,
            "key_points": [
                "Contrast passive AI chatbots with active AI agents",
                "Demonstrate autonomous multi-step execution",
                "Highlight massive industry shift toward agentic workflows",
            ],
            "call_to_action": "Follow @AIUnder60 for daily AI breakdowns!",
        }

        self.sample_idea = ContentIdea(
            topic="Why AI agents are becoming popular",
            title="Why Chatbots Are DEAD (Meet AI Agents)",
            hook="Stop asking ChatGPT questions—that's already outdated.",
            concept="Visual Beat 1: Chatbots only chat. Visual Beat 2: AI agents book flights and execute code. Final Beat: The future is autonomous.",
            target_audience="Tech enthusiasts and developers",
            estimated_duration_seconds=45,
        )

        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name) / "content_briefs"

    def tearDown(self) -> None:
        """Clean up temporary test directory."""
        self.temp_dir.cleanup()

    # ------------------------------------------------------------------
    # Model validation tests
    # ------------------------------------------------------------------

    def test_valid_content_brief_creation(self) -> None:
        """Verify ContentBrief initializes and serializes correctly."""
        brief = ContentBrief(**self.valid_brief_data)
        self.assertEqual(brief.topic, self.valid_brief_data["topic"])
        self.assertEqual(brief.title, self.valid_brief_data["title"])
        self.assertEqual(brief.estimated_duration_seconds, 45)
        self.assertEqual(len(brief.key_points), 3)

        # Test dictionary round-trip
        dict_data = brief.to_dict()
        restored = ContentBrief.from_dict(dict_data)
        self.assertEqual(brief, restored)

        # Test JSON round-trip
        json_str = brief.to_json()
        restored_json = ContentBrief.from_json(json_str)
        self.assertEqual(brief, restored_json)

    def test_empty_required_strings_raise_validation_error(self) -> None:
        """Verify empty required strings raise ContentValidationError."""
        for field in ["topic", "title", "hook", "concept", "target_audience", "call_to_action"]:
            with self.subTest(field=field):
                data = self.valid_brief_data.copy()
                data[field] = ""
                with self.assertRaises(ContentValidationError):
                    ContentBrief(**data)

                data[field] = "   \n\t  "
                with self.assertRaises(ContentValidationError):
                    ContentBrief(**data)

    def test_invalid_duration_values(self) -> None:
        """Verify non-positive durations and durations > 60 raise validation errors."""
        # Zero duration
        data_zero = self.valid_brief_data.copy()
        data_zero["estimated_duration_seconds"] = 0
        with self.assertRaises(ContentValidationError):
            ContentBrief(**data_zero)

        # Negative duration
        data_neg = self.valid_brief_data.copy()
        data_neg["estimated_duration_seconds"] = -10
        with self.assertRaises(ContentValidationError):
            ContentBrief(**data_neg)

        # Exceeding 60 seconds
        data_over = self.valid_brief_data.copy()
        data_over["estimated_duration_seconds"] = 61
        with self.assertRaises(ContentValidationError):
            ContentBrief(**data_over)

        # Non-integer durations (float, string, bool)
        for invalid in [45.5, "45", True, False, None]:
            with self.subTest(invalid=invalid):
                data_type = self.valid_brief_data.copy()
                data_type["estimated_duration_seconds"] = invalid
                with self.assertRaises(ContentValidationError):
                    ContentBrief(**data_type)

    def test_invalid_key_points_type(self) -> None:
        """Verify non-list key_points raise ContentValidationError."""
        for invalid_kp in ["just a string", {"point": 1}, 123, None, True]:
            with self.subTest(invalid_kp=invalid_kp):
                data = self.valid_brief_data.copy()
                data["key_points"] = invalid_kp
                with self.assertRaises(ContentValidationError):
                    ContentBrief(**data)

    def test_empty_key_points_list(self) -> None:
        """Verify key_points list with 0 items raises ContentValidationError."""
        data = self.valid_brief_data.copy()
        data["key_points"] = []
        with self.assertRaises(ContentValidationError):
            ContentBrief(**data)

    def test_empty_key_point_items(self) -> None:
        """Verify empty strings or non-string items within key_points raise error."""
        for bad_item in ["", "   ", None, 123]:
            with self.subTest(bad_item=bad_item):
                data = self.valid_brief_data.copy()
                data["key_points"] = ["Valid point", bad_item]
                with self.assertRaises(ContentValidationError):
                    ContentBrief(**data)

    def test_empty_call_to_action(self) -> None:
        """Verify empty call_to_action raises ContentValidationError."""
        data = self.valid_brief_data.copy()
        data["call_to_action"] = ""
        with self.assertRaises(ContentValidationError):
            ContentBrief(**data)

        data["call_to_action"] = "   "
        with self.assertRaises(ContentValidationError):
            ContentBrief(**data)

    # ------------------------------------------------------------------
    # Conversion tests
    # ------------------------------------------------------------------

    def test_deterministic_idea_to_brief_conversion(self) -> None:
        """Verify content_idea_to_brief deterministically maps idea fields to a brief."""
        brief1 = content_idea_to_brief(self.sample_idea)
        brief2 = content_idea_to_brief(self.sample_idea)

        # Deterministic
        self.assertEqual(brief1, brief2)

        # Preserves existing fields
        self.assertEqual(brief1.topic, self.sample_idea.topic)
        self.assertEqual(brief1.title, self.sample_idea.title)
        self.assertEqual(brief1.hook, self.sample_idea.hook)
        self.assertEqual(brief1.concept, self.sample_idea.concept)
        self.assertEqual(brief1.target_audience, self.sample_idea.target_audience)
        self.assertEqual(brief1.estimated_duration_seconds, self.sample_idea.estimated_duration_seconds)

        # Uses default call to action
        self.assertEqual(brief1.call_to_action, DEFAULT_CALL_TO_ACTION)

        # Extracted key points
        self.assertGreaterEqual(len(brief1.key_points), 1)

    def test_conversion_with_custom_call_to_action(self) -> None:
        """Verify custom call_to_action can be provided during conversion."""
        custom_cta = "Comment 'AGENT' below for our free automation guide!"
        brief = content_idea_to_brief(self.sample_idea, call_to_action=custom_cta)
        self.assertEqual(brief.call_to_action, custom_cta)

    def test_conversion_type_error_on_invalid_input(self) -> None:
        """Verify passing non-ContentIdea to content_idea_to_brief raises TypeError."""
        with self.assertRaises(TypeError):
            content_idea_to_brief({"topic": "Not a ContentIdea"})  # type: ignore

    def test_extract_key_points_beat_markers(self) -> None:
        """Verify heuristic extracts points using beat/step markers."""
        concept = "Visual Beat 1: Intro problem. Visual Beat 2: Demo feature. Final Beat: Summary."
        points = extract_key_points_from_concept(concept)
        self.assertEqual(len(points), 3)
        self.assertIn("Intro problem", points[0])
        self.assertIn("Demo feature", points[1])
        self.assertIn("Summary", points[2])

    def test_extract_key_points_sentence_fallback(self) -> None:
        """Verify heuristic splits sentences when beat markers are absent."""
        concept = "Explain the GIL in Python. Contrast multithreading and multiprocessing; show when each is best."
        points = extract_key_points_from_concept(concept)
        self.assertGreaterEqual(len(points), 2)
        self.assertEqual(points[0], "Explain the GIL in Python")

    def test_extract_key_points_single_sentence(self) -> None:
        """Verify single sentence returns as 1 key point."""
        concept = "A single unbroken concept sentence."
        points = extract_key_points_from_concept(concept)
        self.assertEqual(points, ["A single unbroken concept sentence"])

    # ------------------------------------------------------------------
    # Storage tests
    # ------------------------------------------------------------------

    def test_storage_save_and_load_round_trip(self) -> None:
        """Verify saving and loading ContentBrief JSON files."""
        brief = ContentBrief(**self.valid_brief_data)
        saved_path = save_content_brief(brief, storage_dir=self.storage_dir)

        self.assertTrue(saved_path.is_file())
        self.assertTrue(saved_path.name.endswith(".json"))
        self.assertIn("brief", saved_path.name)

        loaded_brief = load_content_brief(saved_path)
        self.assertEqual(brief, loaded_brief)

    def test_storage_save_does_not_overwrite(self) -> None:
        """Verify multiple saves generate distinct collision-safe filenames."""
        brief = ContentBrief(**self.valid_brief_data)
        path1 = save_content_brief(brief, storage_dir=self.storage_dir)
        path2 = save_content_brief(brief, storage_dir=self.storage_dir)

        self.assertNotEqual(path1, path2)
        self.assertTrue(path1.is_file())
        self.assertTrue(path2.is_file())

    def test_storage_invalid_brief_type(self) -> None:
        """Verify save_content_brief raises StorageError for invalid type."""
        with self.assertRaises(StorageError):
            save_content_brief("not a brief", storage_dir=self.storage_dir)  # type: ignore

    def test_storage_load_missing_file(self) -> None:
        """Verify load_content_brief raises StorageError on missing file."""
        missing = self.storage_dir / "non_existent_brief.json"
        with self.assertRaises(StorageError):
            load_content_brief(missing)

    # ------------------------------------------------------------------
    # CLI tests
    # ------------------------------------------------------------------

    def test_handle_brief_from_idea_cli_missing_arg(self) -> None:
        """Verify CLI handler exits with 1 when path argument is empty."""
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            exit_code = handle_brief_from_idea("")

        self.assertEqual(exit_code, 1)
        self.assertIn("[ERROR]", captured.getvalue())

    def test_handle_brief_from_idea_cli_nonexistent_file(self) -> None:
        """Verify CLI handler exits with 1 when file does not exist."""
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            exit_code = handle_brief_from_idea("non_existent_file_xyz.json")

        self.assertEqual(exit_code, 1)
        self.assertIn("ContentIdea file not found", captured.getvalue())

    def test_handle_brief_from_idea_cli_success(self) -> None:
        """Verify CLI handler reads idea, converts to brief, and saves file."""
        # Write temporary ContentIdea JSON file
        idea_path = Path(self.temp_dir.name) / "test_idea.json"
        idea_path.write_text(self.sample_idea.to_json(), encoding="utf-8")

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            exit_code = handle_brief_from_idea(str(idea_path))

        self.assertEqual(exit_code, 0)
        output = captured.getvalue()
        self.assertIn("AI Under 60 - Content Brief Generator", output)
        self.assertIn("Generated Content Brief:", output)
        self.assertIn("Key Points:", output)
        self.assertIn("Saved to:", output)

    def test_main_cli_brief_from_idea_delegation(self) -> None:
        """Verify main() routes to handle_brief_from_idea when --brief-from-idea is passed."""
        with patch.object(sys, "argv", ["main.py", "--brief-from-idea", "idea.json"]):
            with patch("ai_under_60.main.handle_brief_from_idea", return_value=0) as mock_handle:
                exit_code = main()
                self.assertEqual(exit_code, 0)
                mock_handle.assert_called_once_with("idea.json")


if __name__ == "__main__":
    unittest.main()
