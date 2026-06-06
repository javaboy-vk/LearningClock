@echo off
rem =============================================================================
rem File Name : deploy.cmd
rem Artifact  : LearningClock - Deploy Wrapper
rem Author    : javaboy-vk
rem Date      : 2026-06-05
rem Version   : v0.2.0
rem Purpose:
rem   Runs the Maven-style deploy target.
rem =============================================================================

call "%~dp0dev.cmd" deploy %*
