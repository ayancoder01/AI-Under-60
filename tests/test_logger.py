import logging
from pathlib import Path
import sys
import tempfile
import unittest
import uuid

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.logger import setup_logger



class TestLogger(unittest.TestCase):
    """Test logger initialization, handlers, log levels, and file creation."""

    def setUp(self) -> None:
        """Set up a unique logger name and clean environment for each test."""
        self.logger_name = f"test_logger_{uuid.uuid4().hex}"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.logs_dir = Path(self.temp_dir.name) / "logs"

    def tearDown(self) -> None:
        """Clean up logger handlers and temporary directory."""
        logger = logging.getLogger(self.logger_name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        self.temp_dir.cleanup()

    def test_logger_initialization(self) -> None:
        """Verify the logger initializes with StreamHandler and FileHandler."""
        logger = setup_logger(
            name=self.logger_name,
            log_level="INFO",
            logs_dir=self.logs_dir,
            clear_existing=True,
        )

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, self.logger_name)
        self.assertEqual(logger.level, logging.INFO)

        # Verify both a real StreamHandler (not a FileHandler) and a FileHandler exist
        has_console_stream_handler = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )
        has_file_handler = any(
            isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )

        self.assertTrue(
            has_console_stream_handler,
            "Expected a logging.StreamHandler that is not a logging.FileHandler.",
        )
        self.assertTrue(
            has_file_handler,
            "Expected a logging.FileHandler.",
        )

    def test_logger_configured_level_respected(self) -> None:
        """Verify custom log level (e.g. DEBUG) is set correctly."""
        logger = setup_logger(
            name=self.logger_name,
            log_level="DEBUG",
            logs_dir=self.logs_dir,
            clear_existing=True,
        )

        self.assertEqual(logger.level, logging.DEBUG)

    def test_logger_creates_logs_directory_and_file(self) -> None:
        """Verify logger creates the directory and ai_under_60.log file if not present."""
        self.assertFalse(self.logs_dir.exists())

        setup_logger(
            name=self.logger_name,
            log_level="INFO",
            logs_dir=self.logs_dir,
            clear_existing=True,
        )

        self.assertTrue(self.logs_dir.is_dir())
        log_file = self.logs_dir / "ai_under_60.log"
        self.assertTrue(log_file.is_file())

    def test_logger_writes_message_to_file(self) -> None:
        """Verify logged messages are written to the log file."""
        logger = setup_logger(
            name=self.logger_name,
            log_level="INFO",
            logs_dir=self.logs_dir,
            clear_existing=True,
        )

        test_message = "Test log message verification."
        logger.info(test_message)

        # Flush handlers to ensure content is written to disk
        for handler in logger.handlers:
            handler.flush()

        log_file = self.logs_dir / "ai_under_60.log"
        content = log_file.read_text(encoding="utf-8")
        self.assertIn(test_message, content)
        self.assertIn("[INFO]", content)

    def test_logger_graceful_when_logs_dir_unwritable(self) -> None:
        """Verify setup_logger does not crash if logs directory is invalid."""
        # A file cannot be a directory, creating a conflict for mkdir
        conflict_file = Path(self.temp_dir.name) / "not_a_dir"
        conflict_file.write_text("dummy", encoding="utf-8")
        invalid_logs_dir = conflict_file / "nested_logs"

        logger = setup_logger(
            name=self.logger_name,
            log_level="INFO",
            logs_dir=invalid_logs_dir,
            clear_existing=True,
        )

        self.assertIsInstance(logger, logging.Logger)
        # Should still have the console stream handler even if file handler failed
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        self.assertGreaterEqual(len(stream_handlers), 1)


if __name__ == "__main__":
    unittest.main()
