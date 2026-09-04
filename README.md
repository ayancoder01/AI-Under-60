# AI Under 60

AI Under 60 is an AI-powered YouTube automation system designed to streamline video concept research, scripting, asset generation, editing, and publishing.

> **Current Status**: **Phase 1, Milestone 1.3 - Content Generation Pipeline**
> 
> Milestone 1.3 implements the end-to-end content generation pipeline connecting topic ideation, validation, brief derivation, and artifact persistence in a unified orchestration workflow.
>
> *Note: This milestone establishes the complete content ideation and brief pipeline. Automated research, scripting, voiceover, video rendering, and YouTube publishing are developed in subsequent milestones.*

---

## Project Structure

```text
AI-Under-60/
├── data/
│   ├── content_ideas/              # Stored content idea JSON files (ignored by Git)
│   └── content_briefs/             # Stored content brief JSON files (ignored by Git)
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
│           ├── brief.py            # Idea-to-brief conversion & heuristics
│           ├── idea_generator.py   # Idea generation engine & prompt
│           ├── models.py           # ContentIdea & ContentBrief models
│           ├── pipeline.py         # End-to-end orchestration pipeline
│           └── storage.py          # JSON persistence layer
├── tests/
│   ├── __init__.py
│   ├── test_ai_gemini.py
│   ├── test_config.py
│   ├── test_content_brief.py
│   ├── test_content_models.py
│   ├── test_content_storage.py
│   ├── test_idea_generator.py
│   ├── test_logger.py
│   ├── test_main.py
│   ├── test_package.py
│   └── test_pipeline.py
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
cd "C:\Users\akibu\Desktop\a\AI-Under-60"
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

### 1. Run the Full Content Generation Pipeline (Milestone 1.3)

Run the end-to-end pipeline to generate a validated `ContentIdea`, convert it into a structured `ContentBrief`, and persist both JSON artifacts:

```powershell
python src/ai_under_60/main.py --generate-content "Why AI agents are becoming popular"
```

Or using the `.venv` executable directly:

```powershell
.\.venv\Scripts\python.exe src/ai_under_60/main.py --generate-content "Why AI agents are becoming popular"
```

#### Example Output:

```text
========================================
  AI Under 60 - Content Generation Pipeline
========================================
Topic: Why AI agents are becoming popular
Running end-to-end content generation pipeline...

Pipeline Result:
----------------------------------------
Topic:                      Why AI agents are becoming popular
Title:                      Why Chatbots Are DEAD (Meet AI Agents)
Hook:                       Stop asking ChatGPT questions—that's already outdated.
Target Audience:            Tech enthusiasts, productivity hackers, students, and working professionals
Estimated Duration:         42s
Key Points:
  1. Fast-paced split-screen video contrasting passive AI with active AI
  2. Left side shows chatbot vs right side shows agent booking flight and calendar
  3. Rapid text overlays explaining Autonomy and Execution
  4. On-screen demo of agent executing multi-step tasks
  5. Quick summary of why companies are investing billions into this shift
Call to Action:             Follow @AIUnder60 for more AI insights in under 60 seconds!
----------------------------------------
ContentIdea Saved to:       C:\...\data\content_ideas\20260904_013550_why_ai_agents_are_becoming_popular.json
ContentBrief Saved to:      C:\...\data\content_briefs\20260904_014615_why_ai_agents_are_becoming_popular_brief.json
========================================
```

### 2. Generate a Content Idea Only (Milestone 1.1)

Generate and persist a structured YouTube Short idea:

```powershell
python src/ai_under_60/main.py --generate-idea "Why AI agents are becoming popular"
```

Saved to: `data/content_ideas/<timestamp>_<slug>.json`

### 3. Convert an Existing Idea into a Content Brief (Milestone 1.2)

Convert an existing saved `ContentIdea` into an actionable `ContentBrief`:

```powershell
python src/ai_under_60/main.py --brief-from-idea "data/content_ideas/<your_idea_file>.json"
```

Saved to: `data/content_briefs/<timestamp>_<slug>_brief.json`

### 4. Test Live Gemini API Connection

Verify that your Gemini API credentials and model connection are working:

```powershell
python src/ai_under_60/main.py --test-ai
```

### 5. Application Startup Check (Offline)

Perform standard environment and logger verification without calling external APIs:

```powershell
python src/ai_under_60/main.py
```

### 6. Run the Unit Test Suite

Run all unit tests (fully mocked; zero real API calls or network access required):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### 7. Deactivate the Virtual Environment

When you are finished working:

```powershell
deactivate
```
