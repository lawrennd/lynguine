---
id: "2026-08-19_to-pandas-overlapping-columns"
title: "to_pandas() raises when input and output flows share column names"
status: "Proposed"
priority: "Medium"
created: "2026-08-19"
last_updated: "2026-08-19"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- to_pandas
- join
- overlapping-columns
---

# Task: to_pandas() raises when input and output flows share column names

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

`CustomDataFrame.to_pandas()` joins every stored flow into one DataFrame. When two non-parameter flows share column names, pandas `DataFrame.join` raises:

```
ValueError: columns overlap but no suffix specified: Index(['givenName', ...])
```

This is common in referia configs: `allocation` (input) and `scores` (output) are often the same spreadsheet layout, so they share `givenName`, `Start`, and similar columns.

referia's web `WebReviewer.get_row_data()` used `to_pandas().loc[idx]` to build the Liquid/widget data dict. The overlap error was swallowed as `{}`, so `{{q1Question}}` and other `global_consts` rendered as empty even though the constants Series loaded correctly. Jupyter was unaffected because it uses `get_value()` / `mapping()`.

referia now reads the row with `get_value()` per column (the same path as Jupyter). That is a valid application-layer workaround and should stay. `to_pandas()` itself is still broken for any caller that needs a combined frame.

Triggered by Queens 2021 undergrad admissions and the AI@Cam programme-manager interview configs under `~/OneDrive/referia`.

## Acceptance Criteria

- [ ] `to_pandas()` returns a DataFrame when input and output share column names
- [ ] Overlapping columns have documented, explicit behaviour (suffix, prefer output, or drop duplicates) rather than an unhandled pandas error
- [ ] Parameter columns (constants) are still broadcast onto every row
- [ ] A regression test covers allocation/scores with identical column names
- [ ] Existing `to_pandas()` tests still pass

## Implementation Notes

The join is in `lynguine/assess/data.py` `CustomDataFrame.to_pandas()`:

```python
df1 = df1.join(data, how="outer")
```

Options (pick one and document it; do not leave it implicit):

1. Pass `lsuffix` / `rsuffix` derived from the flow type (`_input`, `_output`).
2. Drop columns from the later frame that already exist (output wins, or input wins).
3. Join only on the index and never duplicate identity columns that already came from an earlier flow.

This is lynguine work. Do not change referia's `get_row_data()` back to `to_pandas()` as part of this task; the per-column `get_value()` path is the right API for the web renderer.

## Related

- Referia workaround: `referia/assess/web_review.py` `WebReviewer.get_row_data()`
- Configs that hit this: `applications/2021-12-06_queens_undergrad-admissions/_referia.yml`, `applications/2024-07-09_ai-cam_programme-manager/interview/_referia.yml`
- Tenet: explicit-infrastructure (`Show me the data flow, make everything explicit`)

## Progress Updates

### 2026-08-19

Task created. referia web Liquid blanks were traced to `to_pandas()` overlap plus `get_row_data()` returning `{}` on any exception. referia workaround is in place; this task is the lynguine fix.
