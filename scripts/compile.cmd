@echo off
rem =============================================================================
rem File Name : compile.cmd
rem Artifact  : LearningClock - Compile Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-05
rem Version   : v0.2.0
rem Purpose:
rem   Runs the Maven-style compile target.
rem =============================================================================

call "%~dp0dev.cmd" compile %*
