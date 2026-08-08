# CSV Contract

The current CSV fields are:

```text
date
learning_path
session_start
session_end
reading
book_listening
outlining
active_recall
sandbox
ai_assisted_architecture_design
ai_assisted_engineering
classical_software_engineering
update_diavgeia
promote_stable_concept
pages_read
total
```

The final row uses:

```text
date = TOTAL
```

The `TOTAL` row aggregates activity durations, page count, and grand total duration across all session rows. Existing `TOTAL` rows are not trusted during rewrite; they are removed and recalculated.

Session rows are written in chronological order by `date` and `session_start`, so a session saved through Set Date is inserted with the corresponding past day.

## Compatibility Rules

- Current canonical date format is `YYYY-MM-DD`.
- Legacy date formats are normalized where supported.
- Legacy `document_in_diavgeia` values map to `update_diavgeia`.
- Legacy `memorizing` values map to `active_recall`.
- Legacy `experimenting` values map to `sandbox`.
- Missing activity duration values are filled as `00:00:00`.
- Missing `pages_read` values are filled as `0`.
- Missing row totals are recalculated from activity columns.
