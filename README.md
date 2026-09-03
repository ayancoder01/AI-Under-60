# AI Under 60

AI Under 60 is an AI-powered YouTube automation system designed to streamline video concept research, scripting, asset generation, editing, and publishing.

> **Current Status**: **Phase 1, Milestone 1.2 - Structured Content Brief**
> 
> Milestone 1.2 implements the structured content brief layer. It takes an existing `ContentIdea` and deterministically converts it into a validated `ContentBrief` with derived key points and a call-to-action, saved under `data/content_briefs/`.
>
> *Note: This milestone establishes the intermediate brief representation between ideation and future research/scriptwriting. Automated research, scripting, voiceover, video rendering, and publishing are developed in subsequent milestones.*

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

Saved to: `data/content_ideas/<timestamp>_<slug>.json`

### 2. Convert an Idea to a Structured Content Brief (Milestone 1.2)

Convert a saved `ContentIdea` into a validated, actionable `ContentBrief`:

```powershell
python src/ai_under_60/main.py --brief-from-idea "data/content_ideas/<your_idea_file>.json"
```

Or using the `.venv` executable directly:

```powershell
.\.venv\Scripts\python.exe src/ai_under_60/main.py --brief-from-idea "data\content_ideas\20260904_013550_why_ai_agents_are_becoming_popular.json"
```

#### Example Output:

```text
========================================
  AI Under 60 - Content Brief Generator
========================================
Source Idea File: data\content_ideas\20260904_013550_why_ai_agents_are_becoming_popular.json

Generated Content Brief:
----------------------------------------
Topic:                      Why AI agents are becoming popular
Title:                      Why Chatbots Are DEAD (Meet AI Agents)
Hook:                       Stop asking ChatGPT questions—that's already outdated. Here is why AI Agents are taking over.
Target Audience:            Tech enthusiasts, productivity hackers, students, and working professionals looking to automate daily tasks.
Estimated Duration:         42s
Key Points:
  1. Fast-paced split-screen video contrasting passive AI (chatbots that just talk) with active AI (agents that do work)
  2. Left side shows a chatbot giving a generic travel itinerary; Right side shows an AI Agent browsing flight sites, booking tickets, and adding events to Google Calendar autonomously
  3. Rapid text overlays explaining 'Autonomy' and 'Execution'
  4. On-screen demo of an agent executing 5 steps in 3 seconds while sound effects build tension
  5. Quick summary of why companies are investing billions into this shift
Call to Action:             Follow @AIUnder60 for more AI insights in under 60 seconds!
----------------------------------------
Saved to:                   C:\Users\akibu\Desktop\AI-Under-60\data\content_briefs\20260904_014615_why_ai_agents_are_becoming_popular_brief.json
========================================
```

#### Generated Content Brief Schema (`data/content_briefs/*.json`):

```json
{
  "topic": "Why AI agents are becoming popular",
  "title": "Why Chatbots Are DEAD (Meet AI Agents)",
  "hook": "Stop asking ChatGPT questions—that's already outdated. Here is why AI Agents are taking over.",
  "concept": "Fast-paced split-screen video contrasting passive AI...",
  "target_audience": "Tech enthusiasts, productivity hackers...",
  "estimated_duration_seconds": 42,
  "key_points": [
    "Fast-paced split-screen video contrasting passive AI with active AI",
    "Left side shows chatbot vs right side shows agent booking flight and calendar",
    "Rapid text overlays explaining Autonomy and Execution",
    "On-screen demo of agent executing multi-step tasks",
    "Quick summary of why companies are investing billions"
  ],
  "call_to_action": "Follow @AIUnder60 for more AI insights in under 60 seconds!"
}
```

### 3. Test Live Gemini API Connection

Verify that your Gemini API credentials and model connection are working:

```powershell
python src/ai_under_60/main.py --test-ai
```

### 4. Application Startup Check (Offline)

Perform standard environment and logger verification without calling external APIs:

```powershell
python src/ai_under_60/main.py
```

### 5. Run the Unit Test Suite

Run all unit tests (fully mocked; zero real API calls or network access required):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### 6. Deactivate the Virtual Environment

When you are finished working:

```powershell
deactivate
```
