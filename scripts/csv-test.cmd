@echo off
rem =============================================================================
rem File Name : csv-test.cmd
rem Artifact  : LearningClock - CSV Regression Test Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-06
rem Version   : v0.1.0
rem Purpose:
rem   Runs one indexed CSV regression test using the default fixture unless --csv is supplied.
rem =============================================================================

call "%~dp0dev.cmd" csv-test %*
