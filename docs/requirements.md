# Requirements

LearningClock is developed and tested as a Windows-friendly Python project.

## Runtime

- Windows
- Python `>=3.11`
- Command Prompt or PowerShell
- Project virtual environment at `.venv`

## Development Dependencies

Development dependencies are declared in `pyproject.toml` under the `dev` optional dependency group:

- `build`
- `debugpy`
- `pygount`
- `pytest`
- `pytest-cov`
- `ruff`

Install the development environment from the repository root:

```cmd
python -m venv .venv
scripts\dev.cmd install
```
