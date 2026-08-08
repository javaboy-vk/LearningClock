# How to add a new timer

This guide shows how to add a new LearningClock timer by following the existing runtime, CSV, test, dashboard, and documentation pattern.

Example timer:

```text
Title: AI-Assisted Architecture & Design
CSV column: ai_assisted_architecture_design
```

## 1. Add the runtime timer

Edit `src/learningclock/csv_store.py`.

In `ACTIVITIES`, add the new activity near the existing AI/software categories:

```python
"AI-Assisted Engineering",
"AI-Assisted Architecture & Design",
"Classical Software Engineering",
```

In `FIELDNAMES`, add the matching CSV column before `classical_software_engineering`:

```python
"ai_assisted_engineering",
"ai_assisted_architecture_design",
"classical_software_engineering",
```

In `ACTIVITY_TO_FIELD`, add the mapping:

```python
"AI-Assisted Engineering": "ai_assisted_engineering",
"AI-Assisted Architecture & Design": "ai_assisted_architecture_design",
"Classical Software Engineering": "classical_software_engineering",
```

Also update the diagnostic log string in `csv_store.py` so saved rows log the new field:

```python
f"ai_assisted_architecture_design={session_row.get('ai_assisted_architecture_design')} | "
```

Put it beside `ai_assisted_engineering`.

## 2. Adjust the app window

Edit `src/learningclock/app.py`.

The UI builds timer rows automatically from `ACTIVITIES`, so the new button will appear without extra widget code. The title is longer and there will be one more row, so increase the fixed geometry and button width.

Suggested geometry changes:

```python
NORMAL_GEOMETRY = "580x460"
ADD_TIME_GEOMETRY = "760x460"
ADD_PAGE_COUNT_GEOMETRY = "680x460"
```

Then increase the activity button width:

```python
width=38,
```

## 3. Update test support defaults

Edit `tests/learning_clock_csv_test_support.py`.

Add the new default field to `row()`:

```python
"ai_assisted_architecture_design": "00:00:00",
```

Place it after `ai_assisted_engineering`.

## 4. Update unit tests

Edit `tests/test_learning_clock_csv_unit.py`.

In `test_create_session_row_formats_fields_and_total`, seed the new timer:

```python
self.clock.totals["AI-Assisted Architecture & Design"] = 240
```

Add an assertion:

```python
self.assertEqual("00:04:00", row["ai_assisted_architecture_design"])
```

Update the expected total from:

```python
"01:06:30"
```

to:

```python
"01:10:30"
```

In `test_create_total_row_sums_activities_pages_and_total`, add a value in one row:

```python
ai_assisted_architecture_design="00:03:00",
```

Add an assertion:

```python
self.assertEqual("00:03:00", total["ai_assisted_architecture_design"])
```

Update that test's expected grand total from:

```python
"00:49:30"
```

to:

```python
"00:52:30"
```

## 5. Update regression QA fixture generation

Edit `tests/test_learning_clock_csv_regression.py`.

In each generated row inside `ensure_default_qa_csv`, add:

```python
"ai_assisted_architecture_design": "00:00:00",
```

For the generated `TOTAL` row, also add the same zero value.

If you choose a non-zero value in those generated rows, recalculate the row `total` and final `TOTAL`. Easiest is to start with `00:00:00`.

## 6. Update static CSV fixtures

Update the header row in:

```text
tests/fixtures/sample_learning_time_log.csv
tests/fixtures/MAGPAI-learning_time_log.csv
```

Insert the new column after `ai_assisted_engineering`:

```text
ai_assisted_engineering,ai_assisted_architecture_design,classical_software_engineering
```

Then add one value for the new column in every data row and the `TOTAL` row. Use:

```text
00:00:00
```

or, in the older MAGPAI style:

```text
0:00:00
```

The parser supports both shapes.

If you use zero values, do not change the existing `total` values.

## 7. Update the dashboard

Edit `diavgeia/LearningClock/views/learning-clock-dashboard/view.js`.

Add the new activity field:

```javascript
["AI-Assisted Engineering", "ai_assisted_engineering"],
["AI-Assisted Architecture & Design", "ai_assisted_architecture_design"],
["Classical Software Engineering", "classical_software_engineering"],
```

Then update both CSS grid definitions from `repeat(9, ...)` to `repeat(10, ...)`:

```css
grid-template-columns: repeat(10, minmax(0, 1fr));
```

They are currently in `.lc-bars` and `.lc-labels`.

## 8. Update docs

Edit `docs/csv-contract.md` and add:

```text
ai_assisted_architecture_design
```

after `ai_assisted_engineering`.

Edit `docs/usage.md` and add the new timer to the tracked activities sentence.

You can also add a short meaning sentence:

```text
`AI-Assisted Architecture & Design` is for architecture, system design, modeling, tradeoff analysis, and design documentation performed with AI assistance.
```

## 9. Regenerate README and docs assets if desired

The README screenshots are SVG assets under `docs/assets`. If you want the visual docs to reflect the new timer, run the project's asset generator after the code change:

```cmd
scripts\readme-assets.cmd
```

## 10. Validate

Run the full tests:

```cmd
scripts\test.cmd
```

Also run the CSV-focused checks if you want faster feedback while editing:

```cmd
scripts\csv-test.cmd test1
scripts\csv-test.cmd test2
scripts\csv-test.cmd test3
scripts\csv-test.cmd test4
```

Finally, launch the app and confirm the new button fits:

```cmd
set PYTHONPATH=src
.\.venv\Scripts\python.exe src\learningclock\app.py --learning-path LearningClock --log-dir build\learning-clock-logs
```

The important invariant is: every visible activity in `ACTIVITIES` must have exactly one CSV field in `FIELDNAMES` and `ACTIVITY_TO_FIELD`. Once that is true, the UI, save path, totals, normalization, and regression tests mostly follow automatically.

## Renaming an existing timer

For a rename such as `Audiobook` to **Book Listening**, update `ACTIVITIES`, `FIELDNAMES`, and `ACTIVITY_TO_FIELD` to the new canonical pair (`Book Listening` / `book_listening`). Add the former column to `LEGACY_FIELD_MAPPINGS` so saved history is normalized instead of discarded, then update the Dataview dashboard field list and run the CSV migration script to rewrite existing headers with backups.
