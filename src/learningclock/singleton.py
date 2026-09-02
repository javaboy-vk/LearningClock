# =============================================================================
# File Name : singleton.py
# Artifact  : LearningClock - Windows Per-Configuration Singleton Guard
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.1
# Purpose:
#   Owns named Windows mutex creation, duplicate rejection, observation, and
#   cleanup as the process-level LearningClock persistence-integrity boundary.
#
# Ownership flow:
#   SingleInstanceGuard(clock_id)
#   |-- construct Local\Protepo.LearningClock.<clock-id>
#   |-- acquire() creates and retains one owned kernel mutex handle
#   |   `-- ERROR_ALREADY_EXISTS closes the temporary handle and rejects startup
#   `-- close() releases ownership and closes the retained handle
#
# Observation flow:
#   is_clock_running(clock_id)
#   |-- OpenMutexW with SYNCHRONIZE access
#   |-- missing name means the clock is available
#   `-- existing name is immediately closed and reported as running
#
# Integrity contract:
#   A clock acquires its guard before persistence initialization. LauncherPad
#   uses only the observation path; process termination remains the final crash
#   cleanup because Windows removes the last kernel handle automatically.
# =============================================================================

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from typing import Any, Protocol

from learningclock.telemetry import (
    DUPLICATE_MUTEX_DETECTED,
    MUTEX_ACQUIRED,
    MUTEX_CLOSED,
    MUTEX_IDENTITY_CONSTRUCTED,
    MUTEX_OBSERVATION_FAILED,
    MUTEX_OPERATION_FAILED,
)

ERROR_ALREADY_EXISTS = 183
SYNCHRONIZE = 0x00100000
MUTEX_NAMESPACE = r"Local\Protepo.LearningClock"


# Source documentation: Returns the stable Windows kernel mutex name for one configured clock.
def mutex_name(clock_id: str) -> str:
    return f"{MUTEX_NAMESPACE}.{clock_id}"


class MutexApi(Protocol):
    """Small injectable boundary around the Windows kernel mutex calls."""

    def create(self, name: str) -> tuple[int, int]: ...

    def open(self, name: str) -> tuple[int, int]: ...

    def release(self, handle: int) -> tuple[bool, int]: ...

    def close(self, handle: int) -> tuple[bool, int]: ...


class WindowsMutexApi:
    """ctypes adapter for CreateMutexW, OpenMutexW, ReleaseMutex, and CloseHandle."""

    # Source documentation:
    #   What it does: Binds the four Win32 mutex functions with explicit ctypes signatures.
    #   Why it exists: Native-call isolation prevents pointer ambiguity and makes ownership logic
    #     depend on an injectable Python protocol.
    #   Designed use: Construct only on Windows; guards create it unless tests inject a fake API.
    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("LearningClock named mutexes require Windows")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.OpenMutexW.restype = wintypes.HANDLE
        kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel32.ReleaseMutex.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32 = kernel32

    def create(self, name: str) -> tuple[int, int]:
        ctypes.set_last_error(0)
        handle = self._kernel32.CreateMutexW(None, True, name)
        return int(handle or 0), ctypes.get_last_error()

    def open(self, name: str) -> tuple[int, int]:
        ctypes.set_last_error(0)
        handle = self._kernel32.OpenMutexW(SYNCHRONIZE, False, name)
        return int(handle or 0), ctypes.get_last_error()

    def release(self, handle: int) -> tuple[bool, int]:
        ctypes.set_last_error(0)
        success = bool(self._kernel32.ReleaseMutex(wintypes.HANDLE(handle)))
        return success, ctypes.get_last_error()

    def close(self, handle: int) -> tuple[bool, int]:
        ctypes.set_last_error(0)
        success = bool(self._kernel32.CloseHandle(wintypes.HANDLE(handle)))
        return success, ctypes.get_last_error()


class SingleInstanceGuard:
    """Retain one configured clock's mutex handle for the full process lifetime."""

    # Source documentation:
    #   What it does: Prepares process-lifetime ownership for one stable clock identity.
    #   Why it exists: Persistence needs one writer per clock while native calls and telemetry
    #     remain replaceable in tests and startup.
    #   Designed use: Create before CsvStore, acquire once, retain for the process, and close at
    #     shutdown; inject api only for deterministic tests.
    def __init__(self, clock_id: str, *, api: MutexApi | None = None, logger: Any = None) -> None:
        self.clock_id = clock_id
        self.name = mutex_name(clock_id)
        self._api = api or WindowsMutexApi()
        self._logger = logger
        self._handle = 0
        if logger is not None:
            logger.event(MUTEX_IDENTITY_CONSTRUCTED, clock_id=clock_id, mutex_name=self.name)

    @property
    def acquired(self) -> bool:
        return bool(self._handle)

    # Source documentation: Rebinds telemetry after startup advances to configured file logging.
    def set_logger(self, logger: Any) -> None:
        self._logger = logger

    # Source documentation:
    #   What it does: Acquires this clock's mutex when no owner already exists.
    #   Why it exists: The mutex prevents two processes from writing the same configured CSV.
    #   Designed use: Call before storage construction; True means ownership, False is an expected
    #     duplicate, and native creation failure raises OSError after telemetry.
    def acquire(self) -> bool:
        if self._handle:
            return True
        handle, error_code = self._api.create(self.name)
        if not handle:
            if self._logger is not None:
                self._logger.event(
                    MUTEX_OPERATION_FAILED,
                    operation_id="CreateMutexW",
                    mutex_name=self.name,
                    error_code=error_code,
                )
            raise OSError(error_code, f"CreateMutexW failed for {self.name}")
        if error_code == ERROR_ALREADY_EXISTS:
            self._api.close(handle)
            if self._logger is not None:
                self._logger.event(
                    DUPLICATE_MUTEX_DETECTED,
                    clock_id=self.clock_id,
                    mutex_name=self.name,
                )
            return False
        self._handle = handle
        if self._logger is not None:
            self._logger.event(MUTEX_ACQUIRED, clock_id=self.clock_id, mutex_name=self.name)
        return True

    # Source documentation:
    #   What it does: Releases owned mutex state during normal shutdown.
    #   Why it exists: Explicit cleanup makes the clock immediately relaunchable; Windows process
    #     teardown remains crash recovery.
    #   Designed use: Call from finally or context-manager cleanup. It is idempotent, logs native
    #     failures, and never restores a stale Python handle.
    def close(self) -> None:
        handle, self._handle = self._handle, 0
        if not handle:
            return
        released, release_error = self._api.release(handle)
        closed, close_error = self._api.close(handle)
        if not released or not closed:
            error_code = release_error if not released else close_error
            if self._logger is not None:
                self._logger.event(
                    MUTEX_OPERATION_FAILED,
                    operation_id="ReleaseMutex/CloseHandle",
                    mutex_name=self.name,
                    error_code=error_code,
                )
            return
        if self._logger is not None:
            self._logger.event(MUTEX_CLOSED, clock_id=self.clock_id, mutex_name=self.name)

    def __enter__(self) -> SingleInstanceGuard:
        if not self.acquire():
            raise RuntimeError(f"LearningClock {self.clock_id!r} is already running")
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()


# Source documentation:
#   What it does: Observes whether a configured clock's mutex currently exists.
#   Why it exists: LauncherPad needs live state across parent restarts and external launches
#     without competing for ownership.
#   Designed use: Poll with a stable clock ID and close the observed handle immediately; missing
#     names return False, while unexpected native errors are logged and raised.
def is_clock_running(
    clock_id: str, *, api: MutexApi | None = None, logger: Any | None = None
) -> bool:
    selected_api = api or WindowsMutexApi()
    name = mutex_name(clock_id)
    handle, error_code = selected_api.open(name)
    if not handle:
        # ERROR_FILE_NOT_FOUND (2) and ERROR_INVALID_NAME (123) mean unavailable, not failure.
        if error_code not in (0, 2, 123):
            error = OSError(error_code, f"OpenMutexW failed for {name}")
            if logger is not None:
                logger.event(
                    MUTEX_OBSERVATION_FAILED,
                    mutex_name=name,
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
            raise error
        return False
    closed, close_error = selected_api.close(handle)
    if not closed:
        if logger is not None:
            error = OSError(close_error, f"CloseHandle failed for observed mutex {name}")
            logger.event(
                MUTEX_OBSERVATION_FAILED,
                mutex_name=name,
                error_type=type(error).__name__,
                error_message=str(error),
            )
        raise OSError(close_error, f"CloseHandle failed for observed mutex {name}")
    return True
