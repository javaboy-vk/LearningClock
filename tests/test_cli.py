# =============================================================================
# File Name : test_cli.py
# Artifact  : LearningClock - CLI Tests
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Verifies the LearningClock CLI behavior.
# =============================================================================

from learningclock.cli import main  # CLI entry point under test.


# Testing algorithm:
#   What we test:
#     Calling the CLI with no arguments uses the default readiness command path.
#   Success:
#     main([]) returns exit code zero and prints the readiness message.
#   Error checks:
#     Assertions catch nonzero exits, missing output, and accidental message changes.
def test_main_prints_ready_message(capsys):
    assert main([]) == 0                                                     # Empty argv should succeed.
    assert capsys.readouterr().out.strip() == "LearningClock is ready."       # Default output is stable.


# Testing algorithm:
#   What we test:
#     Calling the CLI with --version uses the package metadata command path.
#   Success:
#     main(["--version"]) returns exit code zero and prints the package version.
#   Error checks:
#     Assertions catch nonzero exits, missing output, and version-reporting drift.
def test_main_prints_version(capsys):
    assert main(["--version"]) == 0                                          # Version flag should succeed.
    assert capsys.readouterr().out.strip() == "0.1.0"                        # Output matches package version.
