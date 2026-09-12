@echo off
setlocal EnableExtensions

rem =============================================================================
rem File Name : help.bat
rem Artifact  : LearningClock - Project Command Help
rem Author    : javaboy-vk
rem Version   : v1.3.0
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
echo   dev seq-dashboard                Install/update the LearningClock Seq workspace
echo   dev launcherpad                  Start LauncherPad from the source environment
echo   dev launcherpad-register         Register LauncherPad in the current-user Start Menu
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
echo   dev launcherpad
echo   dev launcherpad --config-dir D:\LearningClock\props
echo   dev launcherpad-register
echo   dev launcherpad-register --no-pin
echo   .\.venv\Scripts\pythonw.exe -m learningclock.desktop --clock launcher\dev.properties
echo   dev api --reload
echo   Swagger UI: http://127.0.0.1:8000/docs
echo.
echo Important files:
echo   src\learningclock\app.py          Tkinter desktop timer UI
echo   src\learningclock\launcherpad.py  Primary multi-clock GUI launcher
echo   src\learningclock\singleton.py    Windows named-mutex integrity guard
echo   monitoring\seq                    Seq workspace, dashboard, and installer
echo   src\learningclock\api.py          FastAPI and OpenAPI application
echo   src\learningclock\csv_store.py    CSV schema, persistence, totals, recovery
echo   docs\api.md                        HTTP API and Swagger documentation
echo   docs\convenience-commands.md      Command reference
echo   docs\csv-contract.md              Persisted CSV contract
echo   diavgeia\LearningClock            Diavgeia documentation and dashboard
echo.
