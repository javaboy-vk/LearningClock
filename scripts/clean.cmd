@echo off
rem =============================================================================
rem File Name : clean.cmd
rem Artifact  : LearningClock - Clean Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-05
rem Version   : v0.2.0
rem Purpose:
rem   Runs the Maven-style clean target.
rem =============================================================================

call "%~dp0dev.cmd" clean %*
