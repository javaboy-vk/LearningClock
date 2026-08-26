@echo off
setlocal EnableExtensions

rem =============================================================================
rem File Name : help.bat
rem Artifact  : LearningClock - Project Command Help
rem Author    : javaboy-vk
rem Version   : v0.1.1
rem Purpose:
rem   Shows the local command-line contract for LearningClock.
rem =============================================================================

echo.
echo LearningClock command catalog
echo ============================================================
echo.
echo Standard lifecycle commands:
echo   dev help                         Show this command catalog
echo   dev clean                        Remove generated build/cache output
echo   dev compile                      Byte-compile src and tests
echo   dev validate-config              Validate VS Code and workspace JSON
echo   dev test                         Run the complete pytest suite
echo   dev coverage                     Run tests with terminal and HTML coverage
echo   dev pygount-summary              Generate pygount summary reports
echo   dev readme-assets                Regenerate README SVG assets
echo   dev api --reload                 Run FastAPI with Swagger UI and ReDoc
echo   dev openapi                      Export docs\openapi.json from FastAPI
echo   dev unittest-csv                 Run isolated CSV unit tests
echo   dev unittest-csv-file            Run CSV regression tests
echo   dev csv-test test1               Run one focused CSV regression selector
echo   dev test1                        Run CSV regression test1 wrapper
echo   dev package                      Build package artifacts under build\dist
echo   dev install                      Install runtime and dev requirements into .venv
echo   dev deploy                       Export Diavgeia content to the local vault
echo   dev release                      Copy the production runtime and dashboard
echo   dev all                          Clean, compile, test, and package
echo   dev dev clean                    Dispatch dev.cmd directly when needed
echo.
echo Runtime commands:
echo   set PYTHONPATH=src
echo   .\.venv\Scripts\python.exe src\learningclock\app.py --learning-path LearningClock --log-dir build\learning-clock-logs
echo   dev api --reload
echo   Swagger UI: http://127.0.0.1:8000/docs
echo   wscript.exe //nologo launcher\Learning-clock.vbs launcher\dev.properties
echo.
echo Important files:
echo   src\learningclock\app.py          Tkinter desktop timer UI
echo   src\learningclock\api.py          FastAPI and OpenAPI application
echo   src\learningclock\csv_store.py    CSV schema, persistence, totals, recovery
echo   docs\api.md                        HTTP API and Swagger documentation
echo   docs\convenience-commands.md      Command reference
echo   docs\csv-contract.md              Persisted CSV contract
echo   diavgeia\LearningClock            Diavgeia documentation and dashboard
echo.
