# =============================================================================
# File Name : cli.py
# Artifact  : LearningClock - CLI Entrypoint
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Provides the command-line entrypoint for the LearningClock package.
# =============================================================================

from __future__ import annotations

import argparse

from learningclock import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="learningclock")
    parser.add_argument("--version", action="store_true", help="Print the application version.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    print("LearningClock is ready.")
    return 0
