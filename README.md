# AI Under 60

AI Under 60 is an AI-powered YouTube automation system designed to streamline video concept research, scripting, asset generation, editing, and publishing.

> **Current Status**: **Milestone 0.3 - AI Provider Connection**
> 
> Milestone 0.3 connects the project to the Google Gemini API using the official `google-genai` SDK and the current Interactions API (`gemini-3.6-flash`). It provides a lightweight, secure text-generation wrapper. Note that this milestone only establishes the provider connection; AI agents, workflows, and automated pipeline logic are deferred to subsequent milestones.


---

## Project Structure

```text
AI-Under-60/
├── src/
│   └── ai_under_60/
│       ├── __init__.py
│       ├── config.py
│       ├── logger.py
│       ├── main.py
│       └── ai/
│           ├── __init__.py
│           └── gemini.py
├── tests/
│   ├── __init__.py
│   ├── test_ai_gemini.py
│   ├── test_config.py
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

Install the required dependencies (including the official `google-genai` SDK):

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

### 5. Run the Application (Offline Startup Check)

Run the application using Python from the active virtual environment:

```powershell
python src/ai_under_60/main.py
```

Or using the direct path:

```powershell
.\.venv\Scripts\python.exe src/ai_under_60/main.py
```

*(This verifies local health and configuration readiness without making external API calls).*

### 6. Test the Live Gemini API Connection

To manually test and verify real Gemini API connectivity:

```powershell
python src/ai_under_60/main.py --test-ai
```

Or directly via the provider module:

```powershell
python src/ai_under_60/ai/gemini.py
```

This sends a minimal test prompt (`"Reply with exactly: AI Under 60 connection successful."`) and verifies that the model generates a response.

### 7. Run the Test Suite

Run the full unit test suite (mocked; no external API calls or network access required):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Or from an active virtual environment:

```powershell
python -m unittest discover -s tests -v
```

### 8. Deactivate the Virtual Environment

When you are finished working:

```powershell
deactivate
```
