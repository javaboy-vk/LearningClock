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
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
REGRESSION_PROPERTIES = ROOT / "tests" / "fixtures" / "clock-QA.properties"
PRODUCTION_APP_DIR = Path(r"D:\LearningPath\Tools\LearningClock")


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


def remove_python_metadata() -> None:

    for path in ROOT.rglob("*.egg-info"):
        safe_remove(path)


def dependency_requirements() -> list[str]:

    with (ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)

    project = config.get("project", {})
    requirements = list(project.get("dependencies", []))
    requirements.extend(project.get("optional-dependencies", {}).get("dev", []))
    return requirements


def compile_sources(_args: list[str] | None = None) -> None:

    BUILD_DIR.mkdir(exist_ok=True)
    ok = compileall.compile_dir(ROOT / "src", quiet=1)
    ok = compileall.compile_dir(ROOT / "tests", quiet=1) and ok
    if not ok:
        raise SystemExit(1)


def validate_config(_args: list[str] | None = None) -> None:

    config_files = [
        ROOT / ".vscode" / "launch.json",
        ROOT / ".vscode" / "tasks.json",
        ROOT / "LearningClock.code-workspace",
    ]

    for path in config_files:
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except json.JSONDecodeError as exc:
            relative_path = path.relative_to(ROOT)
            raise SystemExit(
                f"{relative_path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"
            ) from exc
        print(f"valid JSON: {path.relative_to(ROOT)}")


def test(_args: list[str] | None = None) -> None:

    run([require_venv(), "-m", "pytest"])


def coverage(_args: list[str] | None = None) -> None:

    run(
        [
            require_venv(),
            "-m",
            "pytest",
            "--cov=learningclock",
            "--cov-report=term-missing",
            "--cov-report=html:build/coverage/html",
        ]
    )


def pygount_summary(_args: list[str] | None = None) -> None:

    run([require_venv(), str(ROOT / "scripts" / "pygount_summary.py")])


def readme_assets(_args: list[str] | None = None) -> None:

    run([require_venv(), str(ROOT / "scripts" / "generate_readme_assets.py")])


def unittest_csv(args: list[str] | None = None) -> None:

    run([require_venv(), "tests/test_learning_clock_csv_unit.py", *(args or [])])


def unittest_csv_file(args: list[str] | None = None) -> None:

    run([require_venv(), "tests/test_learning_clock_csv_regression.py", *(args or [])])


def csv_test(args: list[str] | None = None) -> None:

    parser = argparse.ArgumentParser(prog="dev.py csv-test")
    parser.add_argument("selector", nargs="?", default="test1")
    parser.add_argument("--properties", default=str(REGRESSION_PROPERTIES))
    parser.add_argument("--csv", default=None)
    parsed_args = parser.parse_args(args or [])
    command = [
        require_venv(),
        "tests/test_learning_clock_csv_regression.py",
        "--properties",
        parsed_args.properties,
    ]
    if parsed_args.csv:
        command.extend(["--csv", parsed_args.csv])
    command.append(parsed_args.selector)
    run(command)


def package(_args: list[str] | None = None) -> None:

    (BUILD_DIR / "dist").mkdir(parents=True, exist_ok=True)
    run([require_venv(), "-m", "build", "--outdir", str(BUILD_DIR / "dist")])
    remove_python_metadata()


def install(_args: list[str] | None = None) -> None:

    py = require_venv()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    requirements = dependency_requirements()
    if requirements:
        run([py, "-m", "pip", "install", *requirements])
    remove_python_metadata()


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


def release(args: list[str] | None = None) -> None:

    parser = argparse.ArgumentParser(prog="dev.py release")
    parser.add_argument("--production-dir", default=str(PRODUCTION_APP_DIR))
    parser.add_argument("--dry-run", action="store_true")
    parsed_args = parser.parse_args(args or [])
    production_dir = Path(parsed_args.production_dir)
    release_files = [
        (
            ROOT / "launcher" / "Learning-Clock.ico",
            production_dir / "Learning-Clock.ico",
        ),
        (
            ROOT / "launcher" / "Learning-clock.vbs",
            production_dir / "Learning-clock.vbs",
        ),
        (
            ROOT / "src" / "learningclock" / "__init__.py",
            production_dir / "__init__.py",
        ),
        (
            ROOT / "src" / "learningclock" / "app.py",
            production_dir / "app.py",
        ),
        (
            ROOT / "src" / "learningclock" / "csv_store.py",
            production_dir / "csv_store.py",
        ),
    ]

    for source, target in release_files:
        if not source.exists():
            raise SystemExit(f"Release source file was not found: {source}")
        if parsed_args.dry_run:
            print(f"would release: {source.relative_to(ROOT)} -> {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"released: {source.relative_to(ROOT)} -> {target}")


def all_targets(_args: list[str] | None = None) -> None:

    clean()
    compile_sources()
    test()
    package()


TARGETS = {
    "clean": clean,
    "compile": compile_sources,
    "validate-config": validate_config,
    "test": test,
    "coverage": coverage,
    "pygount-summary": pygount_summary,
    "readme-assets": readme_assets,
    "unittest-csv": unittest_csv,
    "unittest-csv-file": unittest_csv_file,
    "csv-test": csv_test,
    "package": package,
    "install": install,
    "deploy": deploy,
    "release": release,
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
