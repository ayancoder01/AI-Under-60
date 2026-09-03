import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.config import _load_env_file, get_config



class TestConfig(unittest.TestCase):
    """Test configuration defaults, overrides, and .env parsing."""

    def test_config_defaults(self) -> None:
        """Verify default configuration when no environment variables are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config(load_env=False)
            self.assertEqual(config.app_env, "development")
            self.assertEqual(config.log_level, "INFO")
            self.assertIsInstance(config.project_root, Path)

    def test_config_environment_variable_overrides(self) -> None:
        """Verify environment variables override default settings."""
        env_vars = {
            "APP_ENV": "staging",
            "LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_config(load_env=False)
            self.assertEqual(config.app_env, "staging")
            self.assertEqual(config.log_level, "DEBUG")

    def test_config_log_level_case_insensitive_and_stripped(self) -> None:
        """Verify log level is converted to uppercase and trimmed."""
        env_vars = {
            "LOG_LEVEL": "  warning  ",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_config(load_env=False)
            self.assertEqual(config.log_level, "WARNING")

    def test_config_invalid_log_level_fallback(self) -> None:
        """Verify invalid log levels safely fall back to INFO."""
        env_vars = {
            "LOG_LEVEL": "INVALID_LEVEL_123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_config(load_env=False)
            self.assertEqual(config.log_level, "INFO")

    def test_load_env_file_parses_key_values(self) -> None:
        """Verify _load_env_file loads key-values into environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env.test"
            env_file.write_text(
                "# Comment line\n"
                "APP_ENV=testing\n"
                "LOG_LEVEL=DEBUG\n"
                "EMPTY_LINE_BELOW=\n"
                "\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                _load_env_file(env_file)
                self.assertEqual(os.environ.get("APP_ENV"), "testing")
                self.assertEqual(os.environ.get("LOG_LEVEL"), "DEBUG")

    def test_env_vars_override_env_file(self) -> None:
        """Verify existing environment variables take precedence over .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env.test"
            env_file.write_text("APP_ENV=file_value\n", encoding="utf-8")

            # Pre-set environment variable
            with patch.dict(os.environ, {"APP_ENV": "existing_env_var"}, clear=True):
                _load_env_file(env_file)
                self.assertEqual(os.environ.get("APP_ENV"), "existing_env_var")

    def test_load_env_file_missing_file_handled_gracefully(self) -> None:
        """Verify missing .env file does not raise an error."""
        non_existent_file = Path("non_existent_path_12345/.env")
        try:
            _load_env_file(non_existent_file)
        except Exception as err:  # pylint: disable=broad-except
            self.fail(f"_load_env_file raised an unexpected exception: {err}")


if __name__ == "__main__":
    unittest.main()
