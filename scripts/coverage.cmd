@echo off
rem =============================================================================
rem File Name : coverage.cmd
rem Artifact  : LearningClock - Coverage Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-09
rem Version   : v0.1.0
rem Purpose:
rem   Runs the Maven-style coverage target and writes HTML coverage output.
rem =============================================================================

call "%~dp0dev.cmd" coverage %*
