---
id: "2026-08-19_to-pandas-overlapping-columns"
title: "to_pandas() raises when input and output flows share column names"
status: "In Progress"
priority: "Medium"
created: "2026-08-19"
last_updated: "2026-10-07"
category: "bugs"
related_cips:
- "000E"
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

referia now reads the row with `get_value()` per column (the same path as Jupyter). That is a valid application-layer workaround and should stay. `to_pandas()` itself still needs a documented, reviewed lynguine fix for any caller that needs a combined frame.

Triggered by Queens 2021 undergrad admissions and the AI@Cam programme-manager interview configs under `~/OneDrive/referia`.

## Acceptance Criteria

- [x] `to_pandas()` returns a DataFrame when input and output share column names
- [x] Overlapping columns have documented, explicit behaviour (suffix, prefer output, or drop duplicates) rather than an unhandled pandas error
- [x] Parameter columns (constants) are still broadcast onto every row
- [x] A regression test covers allocation/scores with identical column names
- [ ] Existing `to_pandas()` tests still pass (verify before marking Completed)
- [ ] Behaviour reviewed and accepted (temporary implementation landed without CIP review)

## Implementation Notes

### Temporary implementation (working tree, 2026-10-06)

Landed in `lynguine/assess/data.py` `CustomDataFrame.to_pandas()` (uncommitted as of 2026-10-07):

**Policy chosen: earlier flow wins.** When joining non-parameter flows, columns already present on the left are dropped from the right before `join(how="outer")`. If the right frame has only overlapping columns, join an empty frame on the index to keep index alignment. Parameter flows still use `assign`.

Docstring documents the policy. Regression: `lynguine/tests/test_assess_data.py::test_to_pandas_overlapping_columns_keeps_earlier_flow`.

### Review before closing

- Confirm “earlier flow wins” is correct vs “output wins” for referia allocation/scores (dict iteration order of `self._d` is insertion order from `from_flow`).
- Do not change referia's `get_row_data()` back to `to_pandas()` as part of this task; the per-column `get_value()` path remains the right API for the web renderer.
- Commit only after review; treat current working-tree change as provisional.

## Related

- CIP: [000E](../../cip/cip000E.md) (review required — do not treat provisional policy as Accepted)
- Referia workaround: `referia/assess/web_review.py` `WebReviewer.get_row_data()`
- Related backlog: `2026-10-07_hstack-repeated-rsuffix-collision` (same CIP-000E policy)
- Configs that hit this: Queens undergrad admissions, AI@Cam programme-manager interview
- Tenet: explicit-infrastructure (`Show me the data flow, make everything explicit`)

## Progress Updates

### 2026-08-19

Task created. referia web Liquid blanks were traced to `to_pandas()` overlap plus `get_row_data()` returning `{}` on any exception. referia workaround is in place; this task is the lynguine fix.

### 2026-10-07

Provisional fix implemented in the working tree during a referia load-audit session (should have been backlog-first). Status → In Progress. Documented the “earlier flow wins” policy and regression test. Linked to CIP-000E for review before Accept/commit.
