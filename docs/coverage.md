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

The coverage target runs:

```cmd
pytest --cov=learningclock --cov-report=term-missing --cov-report=html:build/coverage/html
```
