"""Gemini AI provider integration for AI Under 60.

Provides a lightweight wrapper around the official google-genai SDK
using the Interactions API for text generation.
"""

from typing import Any, Optional

from google import genai

try:
    from google.genai._gaos.lib.compat_errors import GeminiNextGenAPIClientError as NextGenAPIError
except ImportError:
    NextGenAPIError = Exception  # type: ignore

try:
    from google.genai.errors import APIError as LegacyAPIError
except ImportError:
    LegacyAPIError = Exception  # type: ignore

from ai_under_60.config import get_config
from ai_under_60.logger import setup_logger

logger = setup_logger("ai_under_60.ai.gemini")

# Tuple of expected API exceptions to catch and wrap
API_ERRORS = (NextGenAPIError, LegacyAPIError)


class GeminiError(Exception):
    """Base exception for all Gemini provider errors."""


class GeminiConfigurationError(GeminiError):
    """Raised when required Gemini configuration or credentials are missing."""


class GeminiAPIError(GeminiError):
    """Raised when an API error occurs during Gemini communication."""


def _extract_text(interaction: Any) -> str:
    """Extract generated text from an Interaction response."""
    if hasattr(interaction, "output_text") and interaction.output_text is not None:
        return str(interaction.output_text)
    if hasattr(interaction, "text") and interaction.text is not None:
        return str(interaction.text)
    if isinstance(interaction, dict):
        if "output_text" in interaction and interaction["output_text"] is not None:
            return str(interaction["output_text"])
        if "text" in interaction and interaction["text"] is not None:
            return str(interaction["text"])
    return ""


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """Initialize and return a Gemini API client using the official google-genai SDK.

    Args:
        api_key: Optional explicit API key. If omitted, loads from application configuration.

    Returns:
        An initialized genai.Client instance.

    Raises:
        GeminiConfigurationError: If no API key is provided or found in the environment.
    """
    if not api_key:
        config = get_config()
        api_key = config.gemini_api_key

    if not api_key or not api_key.strip():
        raise GeminiConfigurationError(
            "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your "
            "environment or .env file."
        )

    logger.debug("Initializing Gemini client with configured API credentials.")
    return genai.Client(api_key=api_key.strip())


def generate_text(
    prompt: str,
    model: Optional[str] = None,
    client: Optional[Any] = None,
) -> str:
    """Generate text using the Gemini Interactions API.

    Args:
        prompt: The input text prompt to send to Gemini.
        model: Model identifier. If None, defaults to configured gemini_model.
        client: Optional pre-configured client instance (used for testing).

    Returns:
        Generated text string.

    Raises:
        ValueError: If prompt is empty or whitespace-only.
        GeminiConfigurationError: If the API key is not configured.
        GeminiAPIError: If the Gemini API call fails.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must not be empty or whitespace only.")

    config = get_config()
    target_model = (model or config.gemini_model).strip()

    if client is None:
        client = get_gemini_client()

    logger.info("Calling Gemini Interactions API with model '%s'.", target_model)

    try:
        interaction = client.interactions.create(
            model=target_model,
            input=prompt,
        )
    except API_ERRORS as err:
        logger.error("Gemini Interactions API call failed: %s", err)
        raise GeminiAPIError(f"Gemini API request failed: {err}") from err

    result_text = _extract_text(interaction)
    logger.debug("Received successful interaction response from Gemini model '%s'.", target_model)
    return result_text


def test_connection() -> int:
    """Verify live Gemini API connectivity with a minimal test prompt.

    Development-only tool that:
    - Reads the API key from environment / .env
    - Sends a test prompt to Gemini via the Interactions API
    - Prints the response without exposing secrets

    Returns:
        0 on success, non-zero on failure.
    """
    config = get_config()
    if not config.is_gemini_configured:
        print("[ERROR] GEMINI_API_KEY is not configured.")
        print("Please copy .env.example to .env and set your GEMINI_API_KEY before running the connection test.")
        return 1

    print(f"Testing Gemini Interactions API connection using model: {config.gemini_model}...")
    test_prompt = "Reply with exactly: AI Under 60 connection successful."

    try:
        response = generate_text(test_prompt)
        print("========================================")
        print("Gemini API Response:")
        print(response.strip())
        print("========================================")
        print("Connection test completed successfully.")
        return 0
    except GeminiError as err:
        print(f"[ERROR] Gemini API connection test failed: {err}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(test_connection())
