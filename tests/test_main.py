import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.main import health_check, main



class TestMain(unittest.TestCase):
    """Test health check and application main entry point."""

    def test_health_check_structure(self) -> None:
        """Verify health_check returns the expected status dictionary."""
        result = health_check()

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "healthy")
        self.assertIn("python_version", result)
        self.assertIn("platform", result)
        self.assertIn("environment", result)
        self.assertIn("log_level", result)
        self.assertTrue(len(result["python_version"]) > 0)

    def test_health_check_reflects_environment(self) -> None:
        """Verify health_check reflects custom environment variables."""
        with patch.dict(os.environ, {"APP_ENV": "staging", "LOG_LEVEL": "WARNING"}):
            result = health_check()
            self.assertEqual(result["environment"], "staging")
            self.assertEqual(result["log_level"], "WARNING")

    def test_main_runs_and_exits_cleanly(self) -> None:
        """Verify main() runs successfully, returns 0, and produces output."""
        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        output = captured_stdout.getvalue()
        self.assertIn("AI Under 60 - YouTube Automation", output)
        self.assertIn("Milestone 0.2 Verification", output)
        self.assertIn("Status: Healthy", output)
        self.assertIn("Startup checks completed successfully.", output)


    def test_main_cli_generate_idea_delegation(self) -> None:
        """Verify main() routes to handle_generate_idea when --generate-idea is passed."""
        with patch.object(sys, "argv", ["main.py", "--generate-idea", "Test Topic"]):
            with patch("ai_under_60.main.handle_generate_idea", return_value=0) as mock_handle:
                exit_code = main()
                self.assertEqual(exit_code, 0)
                mock_handle.assert_called_once_with("Test Topic")

    def test_main_cli_test_ai_delegation(self) -> None:
        """Verify main() routes to test_connection when --test-ai is passed."""
        with patch.object(sys, "argv", ["main.py", "--test-ai"]):
            with patch("ai_under_60.ai.gemini.test_connection", return_value=0) as mock_test_conn:
                exit_code = main()
                self.assertEqual(exit_code, 0)
                mock_test_conn.assert_called_once()


if __name__ == "__main__":
    unittest.main()

