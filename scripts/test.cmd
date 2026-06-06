@echo off
rem =============================================================================
rem File Name : test.cmd
rem Artifact  : LearningClock - Test Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-05
rem Version   : v0.2.0
rem Purpose:
rem   Runs the Maven-style test target.
rem =============================================================================

call "%~dp0dev.cmd" test %*
