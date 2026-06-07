@echo off
rem =============================================================================
rem File Name : test1.cmd
rem Artifact  : LearningClock - CSV Regression Test 1 Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-06
rem Version   : v0.1.0
rem Purpose:
rem   Runs CSV regression test1 against the default fixture.
rem =============================================================================

call "%~dp0dev.cmd" csv-test test1 %*
