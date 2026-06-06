# =============================================================================
# File Name : test_cli.py
# Artifact  : LearningClock - CLI Tests
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Verifies the LearningClock CLI behavior.
# =============================================================================

from learningclock.cli import main


def test_main_prints_ready_message(capsys):
    assert main([]) == 0
    assert capsys.readouterr().out.strip() == "LearningClock is ready."


def test_main_prints_version(capsys):
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == "0.1.0"
