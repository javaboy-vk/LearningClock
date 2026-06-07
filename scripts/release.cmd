@echo off
rem =============================================================================
rem File Name : release.cmd
rem Artifact  : LearningClock - Release Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-06
rem Version   : v0.1.0
rem Purpose:
rem   Copies the launcher and runtime Python files to D:\LearningPath\Tools\LearningClock.
rem =============================================================================

call "%~dp0dev.cmd" release %*
