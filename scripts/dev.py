# =============================================================================
# File Name : dev.py
# Artifact  : LearningClock - Developer Command Runner
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Provides Maven-style lifecycle commands for the Python project.
# =============================================================================

from __future__ import annotations

import argparse
import compileall
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def safe_remove(path: Path) -> None:
    resolved = path.resolve()
    if not str(resolved).startswith(str(ROOT.resolve())):
        raise RuntimeError(f"Refusing to remove outside repository: {resolved}")
    if resolved.is_dir():
        shutil.rmtree(resolved)
    elif resolved.exists():
        resolved.unlink()


def run(args: list[str], *, env: dict[str, str] | None = None) -> None:
    merged_env = os.environ.copy()
    merged_env["PYTHONPATH"] = str(ROOT / "src")
    if env:
        merged_env.update(env)
    subprocess.run(args, cwd=ROOT, env=merged_env, check=True)


def python_executable() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def require_venv() -> str:
    if not VENV_PYTHON.exists():
        raise SystemExit(
            "Missing .venv. Create it first from Command Prompt with: python -m venv .venv"
        )
    return str(VENV_PYTHON)


def clean(_args: list[str] | None = None) -> None:
    for path in [
        BUILD_DIR,
        ROOT / "dist",
        ROOT / ".pytest_cache",
        ROOT / ".ruff_cache",
        ROOT / ".coverage",
    ]:
        safe_remove(path)

    for pattern in ["__pycache__", "*.egg-info"]:
        for path in ROOT.rglob(pattern):
            safe_remove(path)


def compile_sources(_args: list[str] | None = None) -> None:
    BUILD_DIR.mkdir(exist_ok=True)
    ok = compileall.compile_dir(ROOT / "src", quiet=1)
    ok = compileall.compile_dir(ROOT / "tests", quiet=1) and ok
    if not ok:
        raise SystemExit(1)


def test(_args: list[str] | None = None) -> None:
    run([require_venv(), "-m", "pytest"])


def unittest_csv(args: list[str] | None = None) -> None:
    run([require_venv(), "tests/test_learning_clock_csv_unit.py", *(args or [])])


def unittest_csv_file(args: list[str] | None = None) -> None:
    run([require_venv(), "tests/test_learning_clock_csv_regression.py", *(args or [])])


def package(_args: list[str] | None = None) -> None:
    (BUILD_DIR / "dist").mkdir(parents=True, exist_ok=True)
    run([require_venv(), "-m", "build", "--outdir", str(BUILD_DIR / "dist")])


def install(_args: list[str] | None = None) -> None:
    py = require_venv()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-e", ".[dev]"])


def deploy(_args: list[str] | None = None) -> None:
    run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "export-diavgeia-vault.ps1"),
        ]
    )


def all_targets(_args: list[str] | None = None) -> None:
    clean()
    compile_sources()
    test()
    package()


TARGETS = {
    "clean": clean,
    "compile": compile_sources,
    "test": test,
    "unittest-csv": unittest_csv,
    "unittest-csv-file": unittest_csv_file,
    "package": package,
    "install": install,
    "deploy": deploy,
    "all": all_targets,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dev.py")
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    TARGETS[args.target](args.args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
