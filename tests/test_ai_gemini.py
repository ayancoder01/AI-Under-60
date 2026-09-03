"""Unit tests for the Gemini AI provider integration (Interactions API)."""

import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from google.genai._gaos.lib.compat_errors import GeminiNextGenAPIClientError as NextGenAPIError
except ImportError:
    NextGenAPIError = Exception  # type: ignore

from ai_under_60.ai.gemini import (
    GeminiAPIError,
    GeminiConfigurationError,
    _extract_text,
    generate_text,
    get_gemini_client,
    test_connection,
)
from ai_under_60.config import DEFAULT_GEMINI_MODEL, AppConfig, get_config


class TestGeminiProvider(unittest.TestCase):
    """Test suite for Gemini AI integration without contacting real endpoints."""

    def test_default_gemini_model_is_3_6_flash(self) -> None:
        """Verify default Gemini model is configured as gemini-3.6-flash."""
        self.assertEqual(DEFAULT_GEMINI_MODEL, "gemini-3.6-flash")
        config = AppConfig()
        self.assertEqual(config.gemini_model, "gemini-3.6-flash")

    def test_missing_api_key_raises_configuration_error(self) -> None:
        """Verify clear error is raised when GEMINI_API_KEY is not configured."""
        with patch("ai_under_60.ai.gemini.get_config") as mock_get_config:
            mock_get_config.return_value = AppConfig(gemini_api_key=None)
            with self.assertRaises(GeminiConfigurationError) as ctx:
                generate_text("Hello world", client=None)
            self.assertIn("GEMINI_API_KEY is not configured", str(ctx.exception))

    def test_empty_prompt_raises_value_error(self) -> None:
        """Verify empty or whitespace prompt raises ValueError."""
        with self.assertRaises(ValueError):
            generate_text("")
        with self.assertRaises(ValueError):
            generate_text("   \n\t  ")

    def test_config_masks_api_key_in_repr(self) -> None:
        """Verify API key is excluded from configuration string representations."""
        secret_key = "sensitive-gemini-key-xyz99"
        config = AppConfig(gemini_api_key=secret_key)

        self.assertEqual(config.gemini_api_key, secret_key)
        self.assertTrue(config.is_gemini_configured)
        self.assertNotIn(secret_key, repr(config))
        self.assertNotIn(secret_key, str(config))

    def test_config_not_configured_when_key_empty(self) -> None:
        """Verify is_gemini_configured is False when key is None or blank."""
        self.assertFalse(AppConfig(gemini_api_key=None).is_gemini_configured)
        self.assertFalse(AppConfig(gemini_api_key="").is_gemini_configured)
        self.assertFalse(AppConfig(gemini_api_key="   ").is_gemini_configured)

    def test_extract_text_variations(self) -> None:
        """Verify _extract_text extracts text from various response structures."""
        # 1. Interaction with output_text
        mock_interaction = MagicMock()
        mock_interaction.output_text = "Sample output text"
        self.assertEqual(_extract_text(mock_interaction), "Sample output text")

        # 2. Object with text attribute fallback
        mock_text_obj = MagicMock(spec=["text"])
        mock_text_obj.text = "Direct text attribute"
        self.assertEqual(_extract_text(mock_text_obj), "Direct text attribute")

        # 3. Dict with output_text
        self.assertEqual(_extract_text({"output_text": "Dict output text"}), "Dict output text")

        # 4. None / empty
        mock_none = MagicMock(spec=["output_text"])
        mock_none.output_text = None
        self.assertEqual(_extract_text(mock_none), "")

    def test_generate_text_with_mock_interactions_client(self) -> None:
        """Verify generate_text calls client.interactions.create correctly."""
        mock_client = MagicMock()
        mock_interaction = MagicMock()
        mock_interaction.output_text = "AI Under 60 connection successful."
        mock_client.interactions.create.return_value = mock_interaction

        result = generate_text(
            prompt="Ping Gemini",
            model="gemini-3.6-flash",
            client=mock_client,
        )

        self.assertEqual(result, "AI Under 60 connection successful.")
        mock_client.interactions.create.assert_called_once_with(
            model="gemini-3.6-flash",
            input="Ping Gemini",
        )

    def test_generate_text_handles_none_response_text(self) -> None:
        """Verify generate_text safely handles responses where output text is None."""
        mock_client = MagicMock()
        mock_interaction = MagicMock(spec=["output_text"])
        mock_interaction.output_text = None
        mock_client.interactions.create.return_value = mock_interaction

        result = generate_text(prompt="Silent test", client=mock_client)
        self.assertEqual(result, "")

    def test_generate_text_wraps_api_error(self) -> None:
        """Verify API errors during interactions.create are wrapped in GeminiAPIError."""
        mock_client = MagicMock()
        mock_client.interactions.create.side_effect = NextGenAPIError(
            "Resource has been exhausted (quota exceeded)."
        )

        with self.assertRaises(GeminiAPIError) as ctx:
            generate_text("Prompt triggering error", client=mock_client)

        self.assertIn("Resource has been exhausted", str(ctx.exception))

    def test_test_connection_when_unconfigured(self) -> None:
        """Verify test_connection fails gracefully if GEMINI_API_KEY is missing."""
        with patch("ai_under_60.ai.gemini.get_config") as mock_get_config:
            mock_get_config.return_value = AppConfig(gemini_api_key=None)
            captured_stdout = io.StringIO()
            with patch("sys.stdout", captured_stdout):
                code = test_connection()

            self.assertEqual(code, 1)
            self.assertIn("GEMINI_API_KEY is not configured", captured_stdout.getvalue())

    def test_test_connection_success(self) -> None:
        """Verify test_connection succeeds when API call succeeds."""
        with patch("ai_under_60.ai.gemini.get_config") as mock_get_config:
            mock_get_config.return_value = AppConfig(
                gemini_api_key="fake_test_key",
                gemini_model="gemini-3.6-flash",
            )
            with patch(
                "ai_under_60.ai.gemini.generate_text",
                return_value="AI Under 60 connection successful.",
            ):
                captured_stdout = io.StringIO()
                with patch("sys.stdout", captured_stdout):
                    code = test_connection()

                self.assertEqual(code, 0)
                output = captured_stdout.getvalue()
                self.assertIn("AI Under 60 connection successful.", output)
                self.assertIn("Connection test completed successfully.", output)

    def test_test_connection_api_failure(self) -> None:
        """Verify test_connection catches GeminiAPIError and returns code 1."""
        with patch("ai_under_60.ai.gemini.get_config") as mock_get_config:
            mock_get_config.return_value = AppConfig(
                gemini_api_key="fake_test_key",
                gemini_model="gemini-3.6-flash",
            )
            with patch(
                "ai_under_60.ai.gemini.generate_text",
                side_effect=GeminiAPIError("Simulated remote failure"),
            ):
                captured_stdout = io.StringIO()
                with patch("sys.stdout", captured_stdout):
                    code = test_connection()

                self.assertEqual(code, 1)
                output = captured_stdout.getvalue()
                self.assertIn("Simulated remote failure", output)


if __name__ == "__main__":
    unittest.main()
