# Coverage

Generate terminal and HTML coverage:

```cmd
scripts\coverage.cmd
```

Equivalent explicit command:

```cmd
scripts\dev.cmd coverage
```

HTML output is written to:

```text
build\coverage\html\index.html
```

## GitHub Pages

The `.github/workflows/coverage-pages.yml` workflow publishes the HTML coverage report to GitHub Pages on every push to `main` and can also be run manually from the Actions tab.

The repository must have GitHub Pages configured to use GitHub Actions as its publishing source.

The coverage target runs:

```cmd
pytest --cov=learningclock --cov-report=term-missing --cov-report=html:build/coverage/html
```
