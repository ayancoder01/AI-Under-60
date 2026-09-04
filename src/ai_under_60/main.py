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


def handle_generate_idea(topic: str) -> int:
    """Handle CLI command to generate, display, and save a content idea.

    Args:
        topic: The user-specified subject/theme.

    Returns:
        0 on success, non-zero on failure.
    """
    if not topic or not topic.strip():
        print("[ERROR] A non-empty topic must be provided with --generate-idea.")
        print('Example: python src/ai_under_60/main.py --generate-idea "Why AI agents are becoming popular"')
        return 1

    print("========================================")
    print("  AI Under 60 - Content Idea Generator")
    print("========================================")
    print(f"Topic: {topic.strip()}")
    print("Requesting structured idea from Gemini...")

    try:
        from ai_under_60.content import generate_content_idea, save_content_idea

        idea = generate_content_idea(topic)
        saved_path = save_content_idea(idea)

        print("\nGenerated Content Idea:")
        print("----------------------------------------")
        print(f"Title:                      {idea.title}")
        print(f"Hook:                       {idea.hook}")
        print(f"Concept:                    {idea.concept}")
        print(f"Target Audience:            {idea.target_audience}")
        print(f"Estimated Duration:         {idea.estimated_duration_seconds}s")
        print("----------------------------------------")
        print(f"Saved to:                   {saved_path}")
        print("========================================")
        return 0
    except Exception as err:
        print(f"\n[ERROR] Failed to generate content idea: {err}")
        return 1


def handle_brief_from_idea(idea_path_str: str) -> int:
    """Handle CLI command to convert a saved ContentIdea JSON into a ContentBrief.

    Args:
        idea_path_str: Path to the ContentIdea JSON file.

    Returns:
        0 on success, non-zero on failure.
    """
    if not idea_path_str or not idea_path_str.strip():
        print("[ERROR] A path to an existing ContentIdea JSON file must be provided with --brief-from-idea.")
        print('Example: python src/ai_under_60/main.py --brief-from-idea "data/content_ideas/sample.json"')
        return 1

    file_path = Path(idea_path_str.strip())
    if not file_path.is_file():
        print(f"[ERROR] ContentIdea file not found: '{file_path}'.")
        return 1

    print("========================================")
    print("  AI Under 60 - Content Brief Generator")
    print("========================================")
    print(f"Source Idea File: {file_path}")

    try:
        from ai_under_60.content import (
            content_idea_to_brief,
            load_content_idea,
            save_content_brief,
        )

        idea = load_content_idea(file_path)
        brief = content_idea_to_brief(idea)
        saved_path = save_content_brief(brief)

        print("\nGenerated Content Brief:")
        print("----------------------------------------")
        print(f"Topic:                      {brief.topic}")
        print(f"Title:                      {brief.title}")
        print(f"Hook:                       {brief.hook}")
        print(f"Target Audience:            {brief.target_audience}")
        print(f"Estimated Duration:         {brief.estimated_duration_seconds}s")
        print("Key Points:")
        for idx, point in enumerate(brief.key_points, 1):
            print(f"  {idx}. {point}")
        print(f"Call to Action:             {brief.call_to_action}")
        print("----------------------------------------")
        print(f"Saved to:                   {saved_path}")
        print("========================================")
        return 0
    except Exception as err:
        print(f"\n[ERROR] Failed to convert content idea to brief: {err}")
        return 1


def handle_generate_content(topic: str) -> int:
    """Handle CLI command to execute the full content generation pipeline.

    Args:
        topic: The user-specified subject/theme.

    Returns:
        0 on success, non-zero on failure.
    """
    if not topic or not topic.strip():
        print("[ERROR] A non-empty topic must be provided with --generate-content.")
        print('Example: python src/ai_under_60/main.py --generate-content "Why AI agents are becoming popular"')
        return 1

    print("========================================")
    print("  AI Under 60 - Content Generation Pipeline")
    print("========================================")
    print(f"Topic: {topic.strip()}")
    print("Running end-to-end content generation pipeline...")

    try:
        from ai_under_60.content import run_content_pipeline

        result = run_content_pipeline(topic.strip())

        print("\nPipeline Result:")
        print("----------------------------------------")
        print(f"Topic:                      {result.idea.topic}")
        print(f"Title:                      {result.brief.title}")
        print(f"Hook:                       {result.brief.hook}")
        print(f"Target Audience:            {result.brief.target_audience}")
        print(f"Estimated Duration:         {result.brief.estimated_duration_seconds}s")
        print("Key Points:")
        for idx, point in enumerate(result.brief.key_points, 1):
            print(f"  {idx}. {point}")
        print(f"Call to Action:             {result.brief.call_to_action}")
        print("----------------------------------------")
        print(f"ContentIdea Saved to:       {result.idea_path}")
        print(f"ContentBrief Saved to:      {result.brief_path}")
        print("========================================")
        return 0
    except Exception as err:
        print(f"\n[ERROR] Content generation pipeline failed: {err}")
        return 1


def handle_research(topic: str) -> int:
    """Handle CLI command to execute live web research for a given topic.

    Args:
        topic: The user-specified subject/theme.

    Returns:
        0 on success, non-zero on failure.
    """
    if not topic or not topic.strip():
        print("[ERROR] A non-empty topic must be provided with --research.")
        print('Example: python src/ai_under_60/main.py --research "Why AI agents are becoming popular"')
        return 1

    clean_topic = topic.strip()
    print("========================================")
    print("  AI Under 60 - Web Research Engine")
    print("========================================")
    print(f"Topic: {clean_topic}")
    print("Conducting live web research across credible sources...")

    try:
        from ai_under_60.research import (
            ResearchRequest,
            WebResearchProvider,
            save_research_package,
        )

        request = ResearchRequest(
            topic=clean_topic,
            title=clean_topic,
            key_points=[clean_topic],
        )

        provider = WebResearchProvider()
        package = provider.research(request)
        saved_path = save_research_package(package)

        print("\nResearch Summary:")
        print("----------------------------------------")
        print(f"Summary:            {package.summary}")
        print(f"Sources Retrieved:  {len(package.sources)}")
        for idx, src in enumerate(package.sources, 1):
            print(f"  [{idx}] {src.title} ({src.publisher})")
            print(f"      URL: {src.url}")

        print(f"\nClaims Evaluated:   {len(package.claims)}")
        for idx, claim in enumerate(package.claims, 1):
            status_tag = f"[{claim.status.upper()}]"
            print(f"  {idx}. {status_tag} {claim.statement}")
            for ev_idx, ev in enumerate(claim.evidence, 1):
                print(f"     - Evidence {ev_idx} ({ev.source_url}): \"{ev.excerpt[:120]}...\"")

        print("----------------------------------------")
        print(f"Saved to:           {saved_path}")
        print("========================================")
        return 0
    except Exception as err:
        print(f"\n[ERROR] Web research failed: {err}")
        return 1


def main() -> int:
    """Execute initial startup checks and confirmation output."""
    # Ensure UTF-8 output encoding on Windows terminals to safely display emojis and unicode
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if "--test-ai" in sys.argv:
        from ai_under_60.ai.gemini import test_connection
        return test_connection()


    if "--generate-idea" in sys.argv:
        idx = sys.argv.index("--generate-idea")
        topic_arg = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--") else ""
        return handle_generate_idea(topic_arg)

    if "--brief-from-idea" in sys.argv:
        idx = sys.argv.index("--brief-from-idea")
        path_arg = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--") else ""
        return handle_brief_from_idea(path_arg)

    if "--generate-content" in sys.argv:
        idx = sys.argv.index("--generate-content")
        topic_arg = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--") else ""
        return handle_generate_content(topic_arg)

    if "--research" in sys.argv:
        idx = sys.argv.index("--research")
        topic_arg = sys.argv[idx + 1] if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--") else ""
        return handle_research(topic_arg)




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



