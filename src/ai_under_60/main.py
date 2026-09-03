"""Application entry point and health checks for AI Under 60 (Milestone 0.2)."""

import sys
from pathlib import Path
from typing import Any, Dict

# Ensure src directory is in sys.path when running script directly
SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_under_60.config import get_config  # noqa: E402
from ai_under_60.logger import setup_logger  # noqa: E402


def health_check() -> Dict[str, Any]:
    """Verify basic application readiness without contacting external services.

    Verifies:
    - Python runtime is available and healthy
    - Configuration can be loaded
    - Logger can be initialized

    Returns:
        Dict containing status, python version, platform, environment, and log level.
    """
    config = get_config()
    logger = setup_logger("ai_under_60.health_check", log_level=config.log_level)
    logger.debug("Health check invoked successfully.")

    return {
        "status": "healthy",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "environment": config.app_env,
        "log_level": config.log_level,
        "gemini_configured": config.is_gemini_configured,
        "gemini_model": config.gemini_model,
    }


def main() -> int:
    """Execute initial startup checks and confirmation output."""
    if "--test-ai" in sys.argv:
        from ai_under_60.ai.gemini import test_connection
        return test_connection()

    health = health_check()
    config = get_config()
    logger = setup_logger("ai_under_60", log_level=config.log_level)

    logger.info("AI Under 60 is starting...")

    # Confirmation output to console
    print("========================================")
    print("  AI Under 60 - YouTube Automation")
    print("  Milestone 0.2 Verification")
    print("========================================")
    print(f"Status: {health['status'].capitalize()}")
    print(f"Python Version: {health['python_version']} ({health['platform']})")
    print(f"Current Environment: {health['environment']}")
    print(f"Log Level: {health['log_level']}")
    print(f"Gemini Configured: {'Yes' if config.is_gemini_configured else 'No'}")
    print(f"Gemini Model: {config.gemini_model}")
    print("Startup checks completed successfully.")
    print("========================================")

    logger.info("Startup checks completed successfully. Current environment: %s", config.app_env)
    return 0


if __name__ == "__main__":
    sys.exit(main())


