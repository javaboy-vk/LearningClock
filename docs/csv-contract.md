# CSV Contract

The current CSV fields are:

```text
date
learning_path
session_start
session_end
reading
outlining
memorizing
experimenting
audiobook
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

## Compatibility Rules

- Current canonical date format is `YYYY-MM-DD`.
- Legacy date formats are normalized where supported.
- Legacy `document_in_diavgeia` values map to `update_diavgeia`.
- Missing activity duration values are filled as `00:00:00`.
- Missing `pages_read` values are filled as `0`.
- Missing row totals are recalculated from activity columns.
