@echo off
rem =============================================================================
rem File Name : release.cmd
rem Artifact  : LearningClock - Release Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-06
rem Version   : v0.4.0
rem Purpose:
rem   Deploys the application into D:\LearningClock standard subdirectories.
rem =============================================================================

call "%~dp0dev.cmd" release %*
