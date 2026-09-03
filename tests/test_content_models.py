"""Unit tests for ContentIdea data model and validation."""

from pathlib import Path
import sys
import unittest

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.content.models import ContentIdea, ContentValidationError


class TestContentModels(unittest.TestCase):
    """Test suite for ContentIdea validation and serialization."""

    def setUp(self) -> None:
        """Create standard valid attributes for testing."""
        self.valid_data = {
            "topic": "Python Generators",
            "title": "Stop Using Lists! Use Python Generators Instead",
            "hook": "Did you know you can save 90% of your RAM with one keyword?",
            "concept": "Visual demo showing list vs generator memory usage in 40 seconds.",
            "target_audience": "Beginner and intermediate Python developers",
            "estimated_duration_seconds": 45,
        }

    def test_valid_content_idea(self) -> None:
        """Verify ContentIdea can be instantiated with valid data."""
        idea = ContentIdea(**self.valid_data)
        self.assertEqual(idea.topic, "Python Generators")
        self.assertEqual(idea.title, "Stop Using Lists! Use Python Generators Instead")
        self.assertEqual(idea.hook, "Did you know you can save 90% of your RAM with one keyword?")
        self.assertEqual(idea.concept, "Visual demo showing list vs generator memory usage in 40 seconds.")
        self.assertEqual(idea.target_audience, "Beginner and intermediate Python developers")
        self.assertEqual(idea.estimated_duration_seconds, 45)

    def test_serialization_round_trip(self) -> None:
        """Verify to_dict/to_json and from_dict/from_json produce identical models."""
        original = ContentIdea(**self.valid_data)

        # Dictionary round-trip
        dict_data = original.to_dict()
        restored_from_dict = ContentIdea.from_dict(dict_data)
        self.assertEqual(original, restored_from_dict)

        # JSON round-trip
        json_str = original.to_json()
        restored_from_json = ContentIdea.from_json(json_str)
        self.assertEqual(original, restored_from_json)

    def test_empty_topic_raises_validation_error(self) -> None:
        """Verify empty or whitespace topic raises ContentValidationError."""
        data = self.valid_data.copy()
        data["topic"] = ""
        with self.assertRaises(ContentValidationError):
            ContentIdea(**data)

        data["topic"] = "   "
        with self.assertRaises(ContentValidationError):
            ContentIdea(**data)

    def test_empty_required_fields_raise_validation_error(self) -> None:
        """Verify empty required fields raise ContentValidationError."""
        for field in ["title", "hook", "concept", "target_audience"]:
            with self.subTest(field=field):
                data = self.valid_data.copy()
                data[field] = ""
                with self.assertRaises(ContentValidationError):
                    ContentIdea(**data)

                data[field] = "   \n\t "
                with self.assertRaises(ContentValidationError):
                    ContentIdea(**data)

    def test_invalid_duration_zero_or_negative(self) -> None:
        """Verify duration <= 0 raises ContentValidationError."""
        data = self.valid_data.copy()
        data["estimated_duration_seconds"] = 0
        with self.assertRaises(ContentValidationError):
            ContentIdea(**data)

        data["estimated_duration_seconds"] = -15
        with self.assertRaises(ContentValidationError):
            ContentIdea(**data)

    def test_duration_exceeding_sixty_seconds(self) -> None:
        """Verify duration > 60 raises ContentValidationError."""
        data = self.valid_data.copy()
        data["estimated_duration_seconds"] = 61
        with self.assertRaises(ContentValidationError):
            ContentIdea(**data)

        data["estimated_duration_seconds"] = 120
        with self.assertRaises(ContentValidationError):
            ContentIdea(**data)

    def test_valid_boundary_durations(self) -> None:
        """Verify durations at the 1s and 60s boundaries succeed."""
        data_min = self.valid_data.copy()
        data_min["estimated_duration_seconds"] = 1
        idea_min = ContentIdea(**data_min)
        self.assertEqual(idea_min.estimated_duration_seconds, 1)

        data_max = self.valid_data.copy()
        data_max["estimated_duration_seconds"] = 60
        idea_max = ContentIdea(**data_max)
        self.assertEqual(idea_max.estimated_duration_seconds, 60)

    def test_non_integer_duration(self) -> None:
        """Verify float, string, or boolean durations raise ContentValidationError."""
        for invalid_val in [45.5, "45", True, False, None]:
            with self.subTest(val=invalid_val):
                data = self.valid_data.copy()
                data["estimated_duration_seconds"] = invalid_val
                with self.assertRaises(ContentValidationError):
                    ContentIdea(**data)

    def test_from_dict_missing_keys(self) -> None:
        """Verify from_dict raises error when required keys are missing."""
        incomplete_data = {"topic": "AI", "title": "AI Title"}
        with self.assertRaises(ContentValidationError):
            ContentIdea.from_dict(incomplete_data)

    def test_from_json_malformed(self) -> None:
        """Verify from_json raises ContentValidationError on invalid JSON."""
        with self.assertRaises(ContentValidationError):
            ContentIdea.from_json("Not valid JSON at all")


if __name__ == "__main__":
    unittest.main()
