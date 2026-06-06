@echo off
rem =============================================================================
rem File Name : install.cmd
rem Artifact  : LearningClock - Install Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-05
rem Version   : v0.2.0
rem Purpose:
rem   Runs the Maven-style install target.
rem =============================================================================

call "%~dp0dev.cmd" install %*
