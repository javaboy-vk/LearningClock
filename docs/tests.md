# Tests

The test suite lives under `tests\`.

```text
tests\
  test_cli.py                          CLI readiness/version tests.
  test_learning_clock_csv_unit.py      Unit tests for CsvStore and CSV app behavior.
  test_learning_clock_csv_regression.py Regression tests for app-style CSV inputs.
  learning_clock_csv_test_support.py   Shared test harness and deterministic CsvStore adapter.
  fixtures\
    clock-QA.properties                Default QA regression configuration.
    MAGPAI-regression.properties       Explicit MAGPAI regression configuration.
    MAGPAI-learning_time_log.csv       MAGPAI CSV regression fixture.
    sample_learning_time_log.csv       Sample CSV fixture.
```

Run the complete suite:

```cmd
scripts\dev.cmd test
```

Expected current result:

```text
17 passed
```

Run only the CSV unit tests:

```cmd
scripts\dev.cmd unittest-csv
```

Run the default CSV regression tests:

```cmd
scripts\dev.cmd unittest-csv-file
```

Run a specific CSV regression test by index alias:

```cmd
scripts\dev.cmd unittest-csv-file test1
scripts\dev.cmd unittest-csv-file test2
scripts\dev.cmd unittest-csv-file test3
scripts\dev.cmd unittest-csv-file test4
```

Run the MAGPAI-specific regression fixture explicitly:

```cmd
scripts\dev.cmd unittest-csv-file --properties "tests\fixtures\MAGPAI-regression.properties"
```

## Default Clock-QA Regression Fixture

Normal pytest runs use `tests\fixtures\clock-QA.properties` by default. That configuration points to generated QA data under:

```text
build\Clock-QA
```

The regression harness creates or repairs:

```text
build\Clock-QA\learning_time_log.csv
```

The generated CSV is complete: it includes deterministic session rows plus a final `TOTAL` row. `build\` is ignored by Git, so this QA output is reproducible local test data rather than tracked repository data.
