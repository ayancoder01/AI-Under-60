"""Unit tests for content idea JSON storage."""

from pathlib import Path
import sys
import tempfile
import unittest

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.content.models import ContentIdea
from ai_under_60.content.storage import (
    StorageError,
    _slugify,
    load_content_idea,
    save_content_idea,
)


class TestContentStorage(unittest.TestCase):
    """Test suite for content idea file-system storage."""

    def setUp(self) -> None:
        """Create a sample idea and temporary directory for tests."""
        self.sample_idea = ContentIdea(
            topic="Async Python",
            title="Async Python in 50 Seconds",
            hook="Why is your Python code blocking? Let's fix that.",
            concept="Explain asyncio event loop with simple animation.",
            target_audience="Python learners",
            estimated_duration_seconds=50,
        )
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name) / "content_ideas"

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_slugify_helper(self) -> None:
        """Verify slugify produces clean filesystem-safe names."""
        self.assertEqual(_slugify("Why AI Agents Are Popular!"), "why_ai_agents_are_popular")
        self.assertEqual(_slugify("  Spaces & Symbols???  "), "spaces_symbols")
        self.assertEqual(_slugify(""), "content_idea")

    def test_save_creates_directory_and_file(self) -> None:
        """Verify save_content_idea creates missing target directory and file."""
        self.assertFalse(self.storage_dir.exists())

        saved_path = save_content_idea(self.sample_idea, storage_dir=self.storage_dir)

        self.assertTrue(self.storage_dir.is_dir())
        self.assertTrue(saved_path.is_file())
        self.assertTrue(saved_path.name.endswith(".json"))
        self.assertIn("async_python", saved_path.name)

    def test_save_and_load_round_trip(self) -> None:
        """Verify saved content idea can be accurately loaded back."""
        saved_path = save_content_idea(self.sample_idea, storage_dir=self.storage_dir)
        loaded_idea = load_content_idea(saved_path)

        self.assertEqual(self.sample_idea, loaded_idea)

    def test_save_does_not_overwrite_existing_file(self) -> None:
        """Verify multiple saves on the same topic produce distinct filenames."""
        path1 = save_content_idea(self.sample_idea, storage_dir=self.storage_dir)
        path2 = save_content_idea(self.sample_idea, storage_dir=self.storage_dir)

        self.assertNotEqual(path1, path2)
        self.assertTrue(path1.is_file())
        self.assertTrue(path2.is_file())

    def test_save_invalid_type_raises_storage_error(self) -> None:
        """Verify non-ContentIdea passed to save raises StorageError."""
        with self.assertRaises(StorageError):
            save_content_idea("not an idea", storage_dir=self.storage_dir)  # type: ignore

    def test_load_non_existent_file_raises_storage_error(self) -> None:
        """Verify loading missing file raises StorageError."""
        missing = self.storage_dir / "non_existent.json"
        with self.assertRaises(StorageError):
            load_content_idea(missing)

    def test_load_corrupted_file_raises_storage_error(self) -> None:
        """Verify loading corrupted JSON file raises StorageError."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        corrupted = self.storage_dir / "corrupt.json"
        corrupted.write_text("{ incomplete json", encoding="utf-8")

        with self.assertRaises(StorageError):
            load_content_idea(corrupted)


if __name__ == "__main__":
    unittest.main()
