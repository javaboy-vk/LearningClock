#!/usr/bin/env python3
# =============================================================================
# File Name : learning-clock.py
# Artifact  : LearningClock - Compatibility Launcher
# Author    : javaboy-vk
# Date      : 2026-06-06
# Version   : v0.1.0
# Purpose:
#   Preserves existing launcher/debug paths while the implementation lives in
#   learningclock.app and learningclock.csv_store.
# =============================================================================

from learningclock.app import main

if __name__ == "__main__":
    raise SystemExit(main())
