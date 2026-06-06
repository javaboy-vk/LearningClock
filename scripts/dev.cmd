@echo off
rem =============================================================================
rem File Name : dev.cmd
rem Artifact  : LearningClock - Developer Command Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-05
rem Version   : v0.2.0
rem Purpose:
rem   Runs dev.py through the project virtual environment.
rem =============================================================================

setlocal
set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo Missing virtual environment Python: %PYTHON%
    echo Create it first from the project root with: python -m venv .venv
    exit /b 1
)

"%PYTHON%" "%SCRIPT_DIR%dev.py" %*
exit /b %ERRORLEVEL%
