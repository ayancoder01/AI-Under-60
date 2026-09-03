# AI Under 60

AI Under 60 is an AI-powered YouTube automation system designed to streamline video concept research, scripting, asset generation, editing, and publishing.

> **Current Status**: **Milestone 0.2 - Project Verification**
> 
> Milestone 0.2 verifies project readiness with a standard-library test suite, configuration testing, logger isolation, and a lightweight readiness health-check mechanism.

---

## Project Structure

```text
AI-Under-60/
├── src/
│   └── ai_under_60/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       └── logger.py
├── tests/
│   ├── __init__.py
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

### 3. Environment Configuration (Optional)

You can copy `.env.example` to create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Available variables:
- `APP_ENV`: Application environment (default: `development`)
- `LOG_LEVEL`: Logging verbosity (default: `INFO`; choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

### 4. Run the Application

Run the application using Python from the active virtual environment:

```powershell
python src/ai_under_60/main.py
```

Or using the Python module syntax:

```powershell
$env:PYTHONPATH="src"
python -m ai_under_60.main
```

You can also run directly without activating:

```powershell
.\.venv\Scripts\python.exe src/ai_under_60/main.py
```

### 5. Run the Test Suite

Run the unit test suite using Python's built-in `unittest` runner:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Or from an active virtual environment:

```powershell
python -m unittest discover -s tests -v
```

### 6. Deactivate the Virtual Environment

When you are finished working:

```powershell
deactivate
```

