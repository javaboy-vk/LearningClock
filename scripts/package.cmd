@echo off
rem =============================================================================
rem File Name : package.cmd
rem Artifact  : LearningClock - Package Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-05
rem Version   : v0.2.0
rem Purpose:
rem   Runs the Maven-style package target.
rem =============================================================================

call "%~dp0dev.cmd" package %*
