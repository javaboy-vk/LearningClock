# Convenience Commands

Most repository workflows go through `scripts\dev.cmd`, which delegates to `scripts\dev.py`.

```cmd
scripts\dev.cmd clean
scripts\dev.cmd compile
scripts\dev.cmd validate-config
scripts\dev.cmd test
scripts\dev.cmd coverage
scripts\dev.cmd pygount-summary
scripts\dev.cmd readme-assets
scripts\dev.cmd unittest-csv
scripts\dev.cmd unittest-csv-file
scripts\dev.cmd csv-test test1
scripts\dev.cmd package
scripts\dev.cmd install
scripts\dev.cmd deploy
scripts\dev.cmd release
```

Short wrappers are also available:

```cmd
scripts\clean.cmd
scripts\compile.cmd
scripts\test.cmd
scripts\coverage.cmd
scripts\pygount-summary.cmd
scripts\readme-assets.cmd
scripts\csv-test.cmd test1
scripts\test1.cmd
scripts\package.cmd
scripts\install.cmd
scripts\deploy.cmd
scripts\release.cmd
```

## Lifecycle Mapping

- `clean`: remove generated build, cache, coverage, bytecode, and package metadata artifacts.
- `compile`: byte-compile `src` and `tests`.
- `validate-config`: validate `.vscode\launch.json`, `.vscode\tasks.json`, and `LearningClock.code-workspace`.
- `test`: run the complete pytest suite.
- `coverage`: run the complete pytest suite with terminal and HTML coverage.
- `pygount-summary`: generate a pygount summary SVG and keep the README code inventory section at the bottom of the page.
- `readme-assets`: generate README SVG visuals for the desktop UI and Obsidian dashboard.
- `unittest-csv`: run the isolated CSV unit test file.
- `unittest-csv-file`: run the CSV regression suite against a properties-selected or explicitly supplied CSV.
- `csv-test`: run one focused CSV regression selector through the default fixture properties.
- `package`: build package artifacts under `build\dist`.
- `install`: install runtime and development requirements into `.venv`.
- `deploy`: export Diavgeia content to the local vault.
- `release`: copy the production launcher and runtime Python files.
