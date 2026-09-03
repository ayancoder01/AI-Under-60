"""AI Under 60 - YouTube Automation System.

Milestone 0.3: AI Provider Connection (Gemini API).
"""

from ai_under_60.ai.gemini import generate_text
from ai_under_60.main import health_check

__version__ = "0.1.0"
__all__ = ["__version__", "health_check", "generate_text"]


