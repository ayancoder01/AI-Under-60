# AI Under 60

AI Under 60 is an AI-powered YouTube automation system designed to streamline video concept research, scripting, asset generation, editing, and publishing.

> **Current Status**: **Phase 1, Milestone 1.1 - Basic AI Content-Idea Generator**
> 
> Milestone 1.1 implements the first real content-generation feature: generating structured, high-retention video ideas under 60 seconds from a user-provided topic. Output is validated against strict constraints and stored locally as JSON in `data/content_ideas/`.
>
> *Note: This milestone establishes the content-idea generator only. Automated scripting, voiceover, video rendering, YouTube publishing, and autonomous agents are developed in later milestones. Generated ideas require human review.*

---

## Project Structure

```text
AI-Under-60/
├── data/
│   └── content_ideas/              # Stored content idea JSON files
├── src/
│   └── ai_under_60/
│       ├── __init__.py
│       ├── config.py
│       ├── logger.py
│       ├── main.py
│       ├── ai/
│       │   ├── __init__.py
│       │   └── gemini.py           # Gemini Interactions API wrapper
│       └── content/
│           ├── __init__.py
│           ├── idea_generator.py   # Idea generation engine & prompt
│           ├── models.py           # ContentIdea dataclass & validation
│           └── storage.py          # JSON persistence layer
├── tests/
│   ├── __init__.py
│   ├── test_ai_gemini.py
│   ├── test_config.py
│   ├── test_content_models.py
│   ├── test_content_storage.py
│   ├── test_idea_generator.py
│   ├── test_logger.py
│   ├── test_main.py
│   └── test_package.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Prerequisites

- **OS**: Windows 11 (or compatible OS)
- **Python**: Python 3.10+ (Installed with PATH configured)
- **Git**: Git for Windows (optional but recommended)
- **Gemini API Key**: An active API key from Google AI Studio

---

## Getting Started on Windows PowerShell

Open Windows PowerShell and navigate to the project directory:

```powershell
cd "c:\Users\akibu\Desktop\AI-Under-60"
```

### 1. Create the Virtual Environment

If the `.venv` directory does not already exist:

```powershell
python -m venv .venv
```

### 2. Activate the Virtual Environment

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

> **Note**: If you encounter an `Execution_Policies` restriction error in PowerShell, allow local script execution for the current session:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> ```

### 3. Install Dependencies

Install required dependencies (including the official `google-genai` SDK):

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create your local `.env` file from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your credentials:

```ini
APP_ENV=development
LOG_LEVEL=INFO

# Gemini AI Provider Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

> **SECURITY WARNING**:
> * **NEVER** commit your `.env` file to Git or share your API key.
> * `.env` is ignored by `.gitignore` by default. Always verify with `git status` before committing.

---

## Usage

### 1. Generate a Content Idea (Milestone 1.1)

Generate a structured YouTube Short idea for any topic:

```powershell
python src/ai_under_60/main.py --generate-idea "Why AI agents are becoming popular"
```

Or using the direct `.venv` python executable:

```powershell
.\.venv\Scripts\python.exe src/ai_under_60/main.py --generate-idea "Why AI agents are becoming popular"
```

#### Example Output:

```text
========================================
  AI Under 60 - Content Idea Generator
========================================
Topic: Why AI agents are becoming popular
Requesting structured idea from Gemini...

Generated Content Idea:
----------------------------------------
Title:                      Why AI Agents are Taking Over
Hook:                       Chatbots talk, but AI agents actually DO things.
Concept:                    Contrast passive chatbots with autonomous agents executing multi-step tasks.
Target Audience:            Tech enthusiasts, developers, and productivity seekers
Estimated Duration:         45s
----------------------------------------
Saved to:                   c:\Users\akibu\Desktop\AI-Under-60\data\content_ideas\20260904_013000_why_ai_agents_are_becoming_popular.json
========================================
```

#### Generated JSON Schema (`data/content_ideas/*.json`):

```json
{
  "topic": "Why AI agents are becoming popular",
  "title": "Why AI Agents are Taking Over",
  "hook": "Chatbots talk, but AI agents actually DO things.",
  "concept": "Contrast passive chatbots with autonomous agents executing multi-step tasks.",
  "target_audience": "Tech enthusiasts, developers, and productivity seekers",
  "estimated_duration_seconds": 45
}
```

### 2. Test Live Gemini API Connection

Verify that your Gemini API credentials and model connection are working:

```powershell
python src/ai_under_60/main.py --test-ai
```

### 3. Application Startup Check (Offline)

Perform standard environment and logger verification without calling external APIs:

```powershell
python src/ai_under_60/main.py
```

### 4. Run the Unit Test Suite

Run all unit tests (fully mocked; zero real API calls or network access required):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### 5. Deactivate the Virtual Environment

When you are finished working:

```powershell
deactivate
```
