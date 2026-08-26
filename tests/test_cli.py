# =============================================================================
# File Name : test_cli.py
# Artifact  : LearningClock - CLI Tests
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v5.3
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
    captured = capsys.readouterr()
    assert captured.out.strip() == "LearningClock is ready."                 # Default stdout is stable.
    assert "CMDLN-6001 CLI readiness response emitted" in captured.err        # Semantic event uses stderr.


# Testing algorithm:
#   What we test:
#     Calling the CLI with --version uses the package metadata command path.
#   Success:
#     main(["--version"]) returns exit code zero and prints the package version.
#   Error checks:
#     Assertions catch nonzero exits, missing output, and version-reporting drift.
def test_main_prints_version(capsys):

    assert main(["--version"]) == 0                                          # Version flag should succeed.
    captured = capsys.readouterr()
    assert captured.out.strip() == "5.3"                                     # Output matches package version.
    assert "CMDLN-6002 CLI version response emitted for 5.3" in captured.err  # Semantic event uses stderr.
