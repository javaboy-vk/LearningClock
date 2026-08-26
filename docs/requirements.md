# Requirements

LearningClock is developed and tested as a Windows-friendly Python project.

## Runtime

- Windows
- Python `>=3.11`
- Command Prompt or PowerShell
- Project virtual environment at `.venv`
- FastAPI for the HTTP/OpenAPI application
- Uvicorn for serving the HTTP API
- Internal `protepo-log` 0.1.1 distribution, imported as `protepo.log`

The runtime dependency is pinned to the immutable private Git tag in `pyproject.toml`. GitHub
authentication must be available to Git/pip when the dependency is installed; credentials must not
be embedded in the dependency URL.

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
