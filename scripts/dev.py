# =============================================================================
# File Name : dev.py
# Artifact  : LearningClock - Developer Command Runner
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v6.8.0
# Purpose:
#   Provides Maven-style lifecycle commands for the Python project.
#
# Command flow:
#   main(argv)
#   |-- select one TARGETS entry
#   |-- run repository-local clean, compile, test, coverage, documentation,
#   |   packaging, API, Seq, deployment, release, or CSV validation work
#   `-- propagate subprocess failures as a nonzero command result
#
# Safety contract:
#   safe_remove() refuses paths outside the repository. Build products remain
#   under build/ where possible. deploy and release are explicit targets because
#   they write to configured external LearningClock or Diavgeia locations.
# =============================================================================

from __future__ import annotations

import argparse
import compileall
import importlib.util
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
VENV_PYTHONW = ROOT / ".venv" / "Scripts" / "pythonw.exe"
REGRESSION_PROPERTIES = ROOT / "tests" / "fixtures" / "clock-QA.properties"
PRODUCTION_ROOT = Path(r"D:\LearningClock")
PRODUCTION_LIB_DIR = PRODUCTION_ROOT / "Lib"
LEARNINGCLOCK_PROPERTIES_DIR = PRODUCTION_ROOT / "props"
LEARNINGCLOCK_LOG_DIR = PRODUCTION_ROOT / "logs"
LEARNINGCLOCK_ASSETS_DIR = PRODUCTION_ROOT / "assets"
DASHBOARD_MARKDOWN = ROOT / "diavgeia" / "LearningClock" / "Learning-Clock-Dashboard.md"
DASHBOARD_VIEWS_DIR = ROOT / "diavgeia" / "LearningClock" / "views"
DIAVGEIA_LEARNINGCLOCK_DIR = Path(r"D:\DiavgeiaVault\Engineering\LearningClock")
DIAVGEIA_VAULT_ROOT = Path(r"D:\DiavgeiaVault")
LAUNCHER_ICON = ROOT / "launcher" / "Learning-Clock.ico"
REGISTER_LAUNCHERPAD_SCRIPT = ROOT / "scripts" / "Register-LauncherPad.ps1"
WINDOWS_DETACHED_CREATION_FLAGS = 0x00000008 | 0x00000200 | 0x01000000


# Source documentation:
#   What it does: Removes generated content only after proving it is inside this repository.
#   Why it exists: Lifecycle cleanup must never expand into user or production data.
#   Designed use: clean and metadata cleanup pass explicit generated paths; outside paths fail.
def safe_remove(path: Path) -> None:
    resolved = path.resolve()
    if not str(resolved).startswith(str(ROOT.resolve())):
        raise RuntimeError(f"Refusing to remove outside repository: {resolved}")
    if resolved.is_dir():
        shutil.rmtree(resolved)
    elif resolved.exists():
        resolved.unlink()


# Source documentation:
#   What it does: Runs one lifecycle subprocess from the repository with imports enabled.
#   Why it exists: Every command needs the same working directory, PYTHONPATH, and failure policy.
#   Designed use: Targets pass argument lists, never shell strings; nonzero exits raise.
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


# Source documentation:
#   What it does: Returns the project interpreter or stops with bootstrap guidance.
#   Why it exists: Stateful commands must not mutate or depend on an unrelated Python.
#   Designed use: Dependency, test, package, and report targets call it before dispatch.
def require_venv() -> str:
    if not VENV_PYTHON.exists():
        raise SystemExit(
            "Missing .venv. Create it first from Command Prompt with: python -m venv .venv"
        )
    return str(VENV_PYTHON)


# Source documentation:
#   What it does: Returns the project no-console interpreter or stops with setup guidance.
#   Why it exists: LauncherPad must start as a Windows GUI without opening a Python console.
#   Designed use: Launcher and Start Menu registration targets call it after .venv creation.
def require_venv_pythonw() -> str:
    if not VENV_PYTHONW.exists():
        raise SystemExit(
            "Missing .venv GUI Python. Create the environment first with: python -m venv .venv"
        )
    return str(VENV_PYTHONW)


# Source documentation:
#   What it does: Removes generated build, cache, bytecode, and package metadata.
#   Why it exists: Reproducible compilation and packaging need a clean evidence area.
#   Designed use: dev clean and all call it; every deletion is constrained by safe_remove.
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


# Source documentation:
#   What it does: Copies the one dashboard and one Dataview implementation to the vault.
#   Why it exists: All clocks are selected from a single page without generated copies.
#   Designed use: release calls it from packaged runtime assets; tests may override the target.
def export_dashboard_components(
    *,
    source_dir: Path | None = None,
    dashboard_target_dir: Path = DIAVGEIA_VAULT_ROOT,
    views_target_dir: Path = DIAVGEIA_LEARNINGCLOCK_DIR / "views",
    dry_run: bool = False,
) -> None:
    source_root = source_dir or DASHBOARD_MARKDOWN.parent
    source_markdown = source_root / DASHBOARD_MARKDOWN.name
    source_views = source_root / "views"
    if not source_markdown.exists():
        raise SystemExit(f"Dashboard source file was not found: {source_markdown}")
    if not source_views.exists():
        raise SystemExit(f"Dashboard views source folder was not found: {source_views}")

    target_markdown = dashboard_target_dir / source_markdown.name
    target_views = views_target_dir
    obsolete_dashboard = views_target_dir.parent / source_markdown.name
    if dry_run:
        print(f"would export central dashboard: {source_markdown} -> {target_markdown}")
        print(f"would export central dashboard view: {source_views} -> {target_views}")
        if obsolete_dashboard.exists() and obsolete_dashboard.resolve() != target_markdown.resolve():
            print(f"would remove obsolete dashboard location: {obsolete_dashboard}")
        return

    dashboard_target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_markdown, target_markdown)
    shutil.copytree(source_views, target_views, dirs_exist_ok=True)
    if obsolete_dashboard.exists() and obsolete_dashboard.resolve() != target_markdown.resolve():
        obsolete_dashboard.unlink()
        print(f"removed obsolete dashboard location -> {obsolete_dashboard}")
    print(f"exported central dashboard -> {target_markdown}")
    print(f"exported central dashboard view -> {target_views}")


# Source documentation:
#   What it does: Reads runtime and development dependencies from pyproject.toml.
#   Why it exists: dev install must use the package manifest as its single authority.
#   Designed use: Returns PEP 508 strings directly to pip without duplicated versions.
def dependency_requirements() -> list[str]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)

    project = config.get("project", {})
    requirements = list(project.get("dependencies", []))
    requirements.extend(project.get("optional-dependencies", {}).get("dev", []))
    return requirements


# Source documentation:
#   What it does: Byte-compiles product and test Python into the ignored build workflow.
#   Why it exists: Compilation catches syntax problems before slower tests or packaging.
#   Designed use: dev compile and all invoke it; a failed tree produces exit status 1.
def compile_sources(_args: list[str] | None = None) -> None:
    BUILD_DIR.mkdir(exist_ok=True)
    ok = compileall.compile_dir(ROOT / "src", quiet=1)
    ok = compileall.compile_dir(ROOT / "tests", quiet=1) and ok
    if not ok:
        raise SystemExit(1)


# Source documentation:
#   What it does: Validates repository-owned VS Code and workspace JSON files.
#   Why it exists: Malformed editor configuration can break supported workflows unnoticed by tests.
#   Designed use: dev validate-config parses each known file and reports exact diagnostics.
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


# Source documentation:
#   What it does: Runs the suite with terminal and HTML product coverage reports.
#   Why it exists: Coverage is separate evidence from a plain correctness run.
#   Designed use: dev coverage uses the project venv and writes under build/coverage.
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


# Source documentation:
#   What it does: Runs the local FastAPI readiness and documentation server.
#   Why it exists: Developers need one command for health, Swagger UI, ReDoc, and OpenAPI.
#   Designed use: Pass optional host, port, and reload after dev api; defaults use loopback.
def api(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="dev.py api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parsed_args = parser.parse_args(args or [])
    command = [
        require_venv(),
        "-m",
        "uvicorn",
        "learningclock.api:app",
        "--app-dir",
        str(ROOT / "src"),
        "--host",
        parsed_args.host,
        "--port",
        str(parsed_args.port),
    ]
    if parsed_args.reload:
        command.append("--reload")
    run(command)


def openapi(_args: list[str] | None = None) -> None:

    run([require_venv(), str(ROOT / "scripts" / "export_openapi.py")])


# Source documentation:
#   What it does: Invokes the version-controlled Seq workspace installer.
#   Why it exists: Signals, queries, workspace, and dashboard must update together.
#   Designed use: dev seq-dashboard forwards installer arguments and propagates failures.
def seq_dashboard(args: list[str] | None = None) -> None:
    run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "monitoring" / "seq" / "Install-LearningClockSeqDashboard.ps1"),
            *(args or []),
        ]
    )


# Source documentation:
#   What it does: Starts LauncherPad from the repository's no-console Python environment.
#   Why it exists: Developers need one stable command that supplies PYTHONPATH and survives the
#     command dispatcher exiting without tying LauncherPad to a console or shell process.
#   Designed use: Run dev launcherpad with an optional --config-dir; the command returns after
#     creating an independent GUI process and reports its process identifier.
def launcherpad(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="dev.py launcherpad")
    parser.add_argument("--config-dir", default=str(LEARNINGCLOCK_PROPERTIES_DIR))
    parser.add_argument("--central-config", default=None)
    parsed_args = parser.parse_args(args or [])

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    command = [
        require_venv_pythonw(),
        "-m",
        "learningclock.desktop",
        "--config-dir",
        str(Path(parsed_args.config_dir)),
    ]
    if parsed_args.central_config:
        command.extend(["--central-config", str(Path(parsed_args.central_config))])
    creation_flags = WINDOWS_DETACHED_CREATION_FLAGS if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creation_flags,
    )
    print(f"LauncherPad started with process ID {process.pid}.")


# Source documentation:
#   What it does: Creates or updates the current user's LauncherPad Start Menu shortcut.
#   Why it exists: Windows registration needs a stable icon, source command, working directory,
#     and an optional best-effort pin request without changing machine-wide installation state.
#   Designed use: Run dev launcherpad-register after creating .venv; --config-dir controls the
#     shortcut's discovery folder and --no-pin skips the Windows shell pin request.
def register_launcherpad(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="dev.py launcherpad-register")
    parser.add_argument("--config-dir", default=str(LEARNINGCLOCK_PROPERTIES_DIR))
    parser.add_argument("--no-pin", action="store_true")
    parser.add_argument("--central-config", default=None)
    parsed_args = parser.parse_args(args or [])

    pythonw = require_venv_pythonw()
    if not LAUNCHER_ICON.exists():
        raise SystemExit(f"LauncherPad icon was not found: {LAUNCHER_ICON}")
    if not REGISTER_LAUNCHERPAD_SCRIPT.exists():
        raise SystemExit(
            f"LauncherPad registration script was not found: {REGISTER_LAUNCHERPAD_SCRIPT}"
        )

    desktop_arguments = [
        "-m",
        "learningclock.desktop",
        "--config-dir",
        str(Path(parsed_args.config_dir)),
    ]
    if parsed_args.central_config:
        desktop_arguments.extend(["--central-config", str(Path(parsed_args.central_config))])
    shortcut_arguments = subprocess.list2cmdline(desktop_arguments)
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(REGISTER_LAUNCHERPAD_SCRIPT),
        "-TargetPath",
        pythonw,
        "-ShortcutArguments",
        shortcut_arguments,
        "-WorkingDirectory",
        str(ROOT),
        "-IconPath",
        str(LAUNCHER_ICON),
    ]
    if not parsed_args.no_pin:
        command.append("-PinToStart")
    run(command)


def unittest_csv(args: list[str] | None = None) -> None:

    run([require_venv(), "tests/test_learning_clock_csv_unit.py", *(args or [])])


def unittest_csv_file(args: list[str] | None = None) -> None:

    run([require_venv(), "tests/test_learning_clock_csv_regression.py", *(args or [])])


# Source documentation:
#   What it does: Runs one named CSV regression selector against a properties file.
#   Why it exists: Persistence debugging benefits from a fast fixture path beside the full suite.
#   Designed use: dev csv-test accepts a selector and optional properties/CSV paths.
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


# Source documentation:
#   What it does: Builds wheel and source artifacts into the ignored distribution area.
#   Why it exists: Consumers need reproducible artifacts without source-tree egg metadata.
#   Designed use: dev package requires the venv and removes metadata after the build.
def package(_args: list[str] | None = None) -> None:
    (BUILD_DIR / "dist").mkdir(parents=True, exist_ok=True)
    run([require_venv(), "-m", "build", "--outdir", str(BUILD_DIR / "dist")])
    remove_python_metadata()


# Source documentation:
#   What it does: Installs manifest-declared runtime/development dependencies into .venv.
#   Why it exists: The repository needs a predictable environment without editable installation.
#   Designed use: Run after creating .venv; failures stop immediately and metadata is cleaned.
def install(_args: list[str] | None = None) -> None:
    py = require_venv()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    requirements = dependency_requirements()
    if requirements:
        run([py, "-m", "pip", "install", *requirements])
    remove_python_metadata()


# Source documentation:
#   What it does: Publishes the complete LearningClock Diavgeia area.
#   Why it exists: The vault-level dashboard and its view must refresh together.
#   Designed use: Invoke explicitly through dev deploy because it writes outside the repository.
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


def bundled_protepo_source() -> Path:
    """Resolve the installed pure-Python protepo package required by the GUI runtime."""

    specification = importlib.util.find_spec("protepo")
    locations = tuple(specification.submodule_search_locations or ()) if specification else ()
    if not locations:
        raise SystemExit("The release environment does not contain the required protepo package.")
    source = Path(locations[0]).resolve()
    if not source.is_dir():
        raise SystemExit(f"The installed protepo package directory was not found: {source}")
    return source


def remove_obsolete_runtime_directory(
    production_root: Path, *, dry_run: bool = False
) -> None:
    """Remove only the superseded runtime tree within the selected installation root."""

    resolved_root = production_root.resolve()
    obsolete = (resolved_root / "runtime").resolve()
    if obsolete.parent != resolved_root or obsolete.name.casefold() != "runtime":
        raise RuntimeError(f"Refusing unexpected runtime cleanup target: {obsolete}")
    if not obsolete.exists():
        return
    if dry_run:
        print(f"would remove obsolete runtime directory: {obsolete}")
        return
    shutil.rmtree(obsolete)
    print(f"removed obsolete runtime directory: {obsolete}")


# Source documentation:
#   What it does: Stages modules under Lib, configuration under props, and static assets.
#   Why it exists: Production needs every package module while preserving machine configuration.
#   Designed use: Run dev release --dry-run first, then release to an explicit/default directory.
def release(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="dev.py release")
    parser.add_argument("--production-dir", default=str(PRODUCTION_ROOT))
    parser.add_argument("--dry-run", action="store_true")
    parsed_args = parser.parse_args(args or [])
    production_root = Path(parsed_args.production_dir)
    lib_dir = production_root / "Lib"
    protepo_source = bundled_protepo_source()
    release_files = [
        (
            ROOT / "launcher" / "Learning-Clock.ico",
            production_root / "assets" / "Learning-Clock.ico",
        ),
        (
            DASHBOARD_MARKDOWN,
            lib_dir / "learningclock" / "dashboard_assets" / DASHBOARD_MARKDOWN.name,
        ),
        (
            DASHBOARD_VIEWS_DIR / "learning-clock-dashboard" / "view.js",
            lib_dir
            / "learningclock"
            / "dashboard_assets"
            / "views"
            / "learning-clock-dashboard"
            / "view.js",
        ),
    ]
    release_files.extend(
        (source, lib_dir / "learningclock" / source.name)
        for source in sorted((ROOT / "src" / "learningclock").glob("*.py"))
    )

    for source, target in release_files:
        if not source.exists():
            raise SystemExit(f"Release source file was not found: {source}")
        if parsed_args.dry_run:
            print(f"would release: {source.relative_to(ROOT)} -> {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"released: {source.relative_to(ROOT)} -> {target}")

    for directory in (production_root / "props", production_root / "logs"):
        if parsed_args.dry_run:
            print(f"would ensure directory: {directory}")
        else:
            directory.mkdir(parents=True, exist_ok=True)

    protepo_target = lib_dir / "protepo"
    if parsed_args.dry_run:
        print(f"would release runtime dependency: {protepo_source} -> {protepo_target}")
    else:
        shutil.copytree(protepo_source, protepo_target, dirs_exist_ok=True)
        print(f"released runtime dependency: {protepo_source} -> {protepo_target}")

    default_clock_properties = ROOT / "src" / "learningclock" / "clock.properties"
    deployed_clock_properties = lib_dir / "learningclock" / "clock.properties"
    if not default_clock_properties.exists():
        raise SystemExit(f"Release source file was not found: {default_clock_properties}")
    if deployed_clock_properties.exists():
        print(f"preserved configured central file: {deployed_clock_properties}")
    elif parsed_args.dry_run:
        print(
            f"would release: {default_clock_properties.relative_to(ROOT)} -> {deployed_clock_properties}"
        )
    else:
        deployed_clock_properties.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default_clock_properties, deployed_clock_properties)
        print(
            f"released: {default_clock_properties.relative_to(ROOT)} -> {deployed_clock_properties}"
        )

    runtime_dashboard_assets = lib_dir / "learningclock" / "dashboard_assets"
    export_dashboard_components(
        source_dir=None if parsed_args.dry_run else runtime_dashboard_assets,
        dry_run=parsed_args.dry_run,
    )
    remove_obsolete_runtime_directory(production_root, dry_run=parsed_args.dry_run)


# Source documentation:
#   What it does: Runs the local clean, compile, test, and package sequence.
#   Why it exists: Contributors need one deterministic local gate.
#   Designed use: dev all excludes external deployment, release, and live Seq installation.
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
    "api": api,
    "openapi": openapi,
    "seq-dashboard": seq_dashboard,
    "launcherpad": launcherpad,
    "launcherpad-register": register_launcherpad,
    "unittest-csv": unittest_csv,
    "unittest-csv-file": unittest_csv_file,
    "csv-test": csv_test,
    "package": package,
    "install": install,
    "deploy": deploy,
    "release": release,
    "all": all_targets,
}


# Source documentation:
#   What it does: Parses one lifecycle target and dispatches remaining arguments.
#   Why it exists: dev.bat and direct Python use need one authoritative command map.
#   Designed use: Put target first and its options afterward; exceptions preserve nonzero exits.
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dev.py")
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    TARGETS[args.target](args.args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
