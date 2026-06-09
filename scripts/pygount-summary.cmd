@echo off
rem =============================================================================
rem File Name : pygount-summary.cmd
rem Artifact  : LearningClock - Pygount Summary Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-09
rem Version   : v0.1.0
rem Purpose:
rem   Generates a pygount summary SVG and updates the README Code Inventory section.
rem =============================================================================

call "%~dp0dev.cmd" pygount-summary %*
