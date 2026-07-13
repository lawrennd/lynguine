---
id: "2026-07-13_bool-to-float64-dtype-write-failure"
title: "Boolean values fail to write into float64 columns (checkbox presence flags)"
status: "Completed"
priority: "High"
created: "2026-07-13"
last_updated: "2026-07-13"
category: "bugs"
related_cips: []
owner: "neil"
dependencies: []
tags:
- backlog
- dtype
- pandas
- checkbox
- excel
---

# Task: Boolean values fail to write into float64 columns

## Description

When a checkbox widget (e.g. a presence flag such as `ch1Present`) was ticked in a
Jupyter notebook, the value `True` failed to persist and the column in the output
spreadsheet was left unchanged. The error was silently swallowed in the UI, but
logged as:

```
ERROR:referia.util.widgets: Invalid value 'True' for dtype 'float64'
```

**Root cause:** pandas infers a column as `float64` whenever any row contains a
blank/NaN value (common when a new boolean column is added to an existing Excel
file). With `raise_on_upcast=True` (the pandas default since 2.x), attempting to
write a Python `bool` into a `float64` column raises a `TypeError` instead of
silently upcasting.

The failure path was:

```
FieldWidget.on_value_change (referia/util/widgets.py:647)
  → DataObject.set_value (lynguine/assess/data.py:566)
    → CustomDataFrame.__setitem__ (lynguine/assess/data.py:2688)
      → data.at[row_label, col_label] = value   ← TypeError raised here
```

Because the error was caught and logged in the widget layer but not re-raised, the
user saw no visible feedback — the checkbox appeared to work but the value was
never stored.

## Acceptance Criteria

- [x] Ticking a boolean checkbox saves correctly even when the column was loaded as
  `float64` due to blank rows in the source spreadsheet.
- [x] `True` is stored as `1.0` and `False` as `0.0` (Excel-compatible representation).
- [x] `visible_if` conditions that test these columns continue to evaluate correctly
  (non-zero floats are truthy).
- [x] Non-boolean type mismatches fall back to upcasting the column to `object`
  dtype rather than silently discarding the write.
- [x] No regressions in existing tests.

## Implementation Notes

Added a `_set_value_with_coercion(data, row_label, col_label, value)` module-level
helper in `lynguine/assess/data.py`. The helper wraps the bare
`data.at[row_label, col_label] = value` assignment:

1. **First attempt** — try the assignment as-is (zero overhead for the common case
   where dtypes match).
2. **Bool → float64 coercion** — if a `TypeError`/`ValueError` is raised and the
   value is a Python `bool` and the column is `float64`, write `float(value)`
   instead. This matches how Excel natively stores boolean values and keeps
   `visible_if` truthiness evaluation intact.
3. **Generic fallback** — for any other type mismatch, upcast the column to
   `object` dtype and retry.

Both `data.at[...]` call sites in `CustomDataFrame.__setitem__` (lines 2688 and
2693 in the original file) were updated to use the helper.

## Related

- PRs: —
- Documentation: —

## Progress Updates

### 2026-07-13

Bug identified from repeated `ERROR:referia.util.widgets: Invalid value 'True' for
dtype 'float64'` entries in `pdfpages/lynguine.log`. Fix implemented in
`lynguine/assess/data.py` by introducing `_set_value_with_coercion`. Status set to
Completed.
