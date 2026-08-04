@echo off
setlocal EnableExtensions

rem =============================================================================
rem File Name : dev.bat
rem Artifact  : LearningClock - Root Developer Command Dispatcher
rem Author    : javaboy-vk
rem Version   : v0.1.1
rem Purpose:
rem   Dispatches root-level dev commands to scripts\*.cmd or scripts\dev.cmd.
rem =============================================================================

set "ROOT=%~dp0"
set "COMMAND=%~1"

if "%COMMAND%"=="" (
    call "%ROOT%help.bat"
    exit /b %ERRORLEVEL%
)

if /I "%COMMAND%"=="help" (
    call "%ROOT%help.bat"
    exit /b %ERRORLEVEL%
)

if "%COMMAND%"=="/?" (
    call "%ROOT%help.bat"
    exit /b %ERRORLEVEL%
)

set "SCRIPT_COMMAND=%ROOT%scripts\%COMMAND%.cmd"

if exist "%SCRIPT_COMMAND%" (
    call "%SCRIPT_COMMAND%" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

call "%ROOT%scripts\dev.cmd" %*
exit /b %ERRORLEVEL%
