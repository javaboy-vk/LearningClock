# =============================================================================
# File Name : test_singleton.py
# Artifact  : LearningClock - Named Mutex Singleton Tests
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.0
# Purpose:
#   Verifies per-clock mutex ownership, observation, duplicate rejection, and
#   Windows process-exit cleanup without lock files.
# =============================================================================

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest

from learningclock.singleton import (
    ERROR_ALREADY_EXISTS,
    SingleInstanceGuard,
    is_clock_running,
    mutex_name,
)


class FakeMutexApi:
    def __init__(self):
        self.names: set[str] = set()
        self.handles: dict[int, tuple[str, bool]] = {}
        self.next_handle = 1

    def _handle(self, name: str, owner: bool) -> int:
        handle = self.next_handle
        self.next_handle += 1
        self.handles[handle] = (name, owner)
        return handle

    def create(self, name):
        if name in self.names:
            return self._handle(name, False), ERROR_ALREADY_EXISTS
        self.names.add(name)
        return self._handle(name, True), 0

    def open(self, name):
        return (self._handle(name, False), 0) if name in self.names else (0, 2)

    def release(self, handle):
        return (handle in self.handles, 0)

    def close(self, handle):
        item = self.handles.pop(handle, None)
        if item is None:
            return False, 6
        name, owner = item
        if owner:
            self.names.discard(name)
        return True, 0


def test_duplicate_same_clock_is_rejected_and_different_ids_coexist():
    api = FakeMutexApi()
    magpai = SingleInstanceGuard("magpai", api=api)
    duplicate = SingleInstanceGuard("magpai", api=api)
    dias = SingleInstanceGuard("dias", api=api)

    assert magpai.acquire() is True
    assert duplicate.acquire() is False
    assert dias.acquire() is True
    assert is_clock_running("magpai", api=api) is True
    assert is_clock_running("dias", api=api) is True

    magpai.close()
    dias.close()
    assert is_clock_running("magpai", api=api) is False
    assert is_clock_running("dias", api=api) is False
    assert mutex_name("magpai") == r"Local\Protepo.LearningClock.magpai"


@pytest.mark.skipif(os.name != "nt", reason="Windows kernel mutex integration")
def test_windows_mutex_disappears_when_owning_process_exits():
    clock_id = f"pytest-{uuid4().hex}"
    source_root = Path(__file__).resolve().parents[1] / "src"
    code = (
        "from learningclock.singleton import SingleInstanceGuard; "
        f"guard=SingleInstanceGuard('{clock_id}'); "
        "assert guard.acquire(); print('READY', flush=True); input(); guard.close()"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source_root)
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "READY"
        assert is_clock_running(clock_id) is True
        duplicate = SingleInstanceGuard(clock_id)
        assert duplicate.acquire() is False
        assert process.stdin is not None
        process.stdin.write("\n")
        process.stdin.flush()
        process.wait(timeout=5)
        deadline = time.monotonic() + 2
        while is_clock_running(clock_id) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert is_clock_running(clock_id) is False
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

