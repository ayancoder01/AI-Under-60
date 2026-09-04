# AI Under 60

AI Under 60 is an AI-powered YouTube automation system designed to streamline video concept research, scripting, asset generation, editing, and publishing.

> **Current Status**: **Phase 1, Milestone 1.5 - Live Web Research Provider**
> 
> Milestone 1.5 implements live web research capabilities via `WebResearchProvider`. It retrieves real web documents via HTTP search, extracts readable page text, derives factual evidence excerpts, conservatively assesses claims, and stores research packages in `data/research/`.
>
> *Strict Integrity Rule: This system never fabricates URLs, publishers, titles, excerpts, or citations. All sources and evidence originate from actual retrieved web content. Claims without evidence remain strictly unsupported.*

---

## Project Structure

```text
AI-Under-60/
├── data/
│   ├── content_ideas/              # Stored content idea JSON files (ignored by Git)
│   ├── content_briefs/             # Stored content brief JSON files (ignored by Git)
│   └── research/                   # Stored research package JSON files (ignored by Git)
├── src/
│   └── ai_under_60/
│       ├── __init__.py
│       ├── config.py
│       ├── logger.py
│       ├── main.py
│       ├── ai/
│       │   ├── __init__.py
│       │   └── gemini.py           # Gemini Interactions API wrapper
│       ├── content/
│       │   ├── __init__.py
│       │   ├── brief.py            # Idea-to-brief conversion & heuristics
│       │   ├── idea_generator.py   # Idea generation engine & prompt
│       │   ├── models.py           # ContentIdea & ContentBrief models
│       │   ├── pipeline.py         # End-to-end orchestration pipeline
│       │   └── storage.py          # JSON persistence layer
│       └── research/
│           ├── __init__.py
│           ├── models.py           # Source, Evidence, Claim, ResearchPackage models
│           ├── provider.py         # ResearchProvider protocol & MockResearchProvider
│           ├── request.py          # ResearchRequest & ContentBrief conversion
│           ├── storage.py          # Research package JSON persistence
│           └── web.py              # WebResearchProvider (search & page fetch)
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
│   ├── test_pipeline.py
│   ├── test_research.py
│   └── test_web_research.py
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

## Research Engine (Milestones 1.4 & 1.5)

The research layer establishes an evidence contract for validating claims against real web information:

### Core Data Models
* **`Source`**: Represents an external document (`title`, `url`, `publisher`, `retrieved_at`).
* **`Evidence`**: Factual excerpt extracted from a source (`source_url`, `excerpt`, `relevance`).
* **`Claim`**: Factual assertion with evaluation status (`supported`, `contradicted`, `uncertain`, `unsupported`) and supporting evidence list.
* **`ResearchPackage`**: Aggregated research findings (`topic`, `sources`, `claims`, `summary`), saved to `data/research/`.
* **`ResearchRequest`**: Deterministic query specification derived from `ContentBrief` (`create_research_request(brief)`).

### Provider Architecture
* **`ResearchProvider`**: Protocol decoupling evidence gathering from downstream consumers.
* **`MockResearchProvider`**: Offline mock provider for testing without external services.
* **`WebResearchProvider`**: Live research provider executing bounded HTTP search, page fetching, clean text extraction, and conservative evidence verification without browser automation or external scraping frameworks.

### Integrity & Testing
* **Integrity Guarantee**: Never invents facts, citations, or URLs. Claims without verified matching excerpts are marked `unsupported`.
* **Offline Unit Tests**: All unit tests mock the network layer, verifying 100% of pipeline logic offline with zero network dependency.
* **Live Verification**: Live CLI execution performs real HTTP requests to gather real web evidence.

---

## Usage

### 1. Conduct Live Web Research (Milestone 1.5)

Run live web research on any topic to retrieve real web sources and evaluate claims:

```powershell
python src/ai_under_60/main.py --research "Why AI agents are becoming popular"
```

Saved to: `data/research/<timestamp>_<slug>_research.json`

### 2. Run the Content Generation Pipeline (Milestone 1.3)

Run the end-to-end pipeline to generate a validated `ContentIdea`, convert it into a structured `ContentBrief`, and persist both JSON artifacts:

```powershell
python src/ai_under_60/main.py --generate-content "Why AI agents are becoming popular"
```

### 3. Generate a Content Idea Only (Milestone 1.1)

Generate and persist a structured YouTube Short idea:

```powershell
python src/ai_under_60/main.py --generate-idea "Why AI agents are becoming popular"
```

Saved to: `data/content_ideas/<timestamp>_<slug>.json`

### 4. Convert an Existing Idea into a Content Brief (Milestone 1.2)

Convert an existing saved `ContentIdea` into an actionable `ContentBrief`:

```powershell
python src/ai_under_60/main.py --brief-from-idea "data/content_ideas/<your_idea_file>.json"
```

Saved to: `data/content_briefs/<timestamp>_<slug>_brief.json`

### 5. Test Live Gemini API Connection

Verify that your Gemini API credentials and model connection are working:

```powershell
python src/ai_under_60/main.py --test-ai
```

### 6. Application Startup Check (Offline)

Perform standard environment and logger verification without calling external APIs:

```powershell
python src/ai_under_60/main.py
```

### 7. Run the Unit Test Suite

Run all unit tests (fully mocked; zero real API calls or network access required):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### 8. Deactivate the Virtual Environment

When you are finished working:

```powershell
deactivate
```
