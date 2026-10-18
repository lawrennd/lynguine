---
id: "2026-10-18_at-setitem-empty-output-steals-cache"
title: "CustomDataFrame.at writes into empty output instead of cache (dict soft-fill lost)"
status: "Completed"
priority: "High"
created: "2026-10-18"
last_updated: "2026-10-18"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- cache
- AtAccessor
- soft-fill
- extract_form_fields
---

# Bug: `.at` must route writes by colspecs, not first empty store

> Discovered while fixing referia CoE
> `2026-10-18_web-reviewer-skips-precompute-soft-fill` (Panel soft-fill).

## Description

`CustomDataFrame._AtAccessor.__setitem__` iterated `_d` and, when the row was
missing from a store, wrote into that store. With an **empty `output` index**
(headers-only CSV) and a new **`cache`** column (e.g. `applicant` for
`extract_form_fields`), the write landed on `output` while `coltype` /
`get_value` still read **`cache`** → callers saw `None` after a successful
set. Dict payloads (form extract) were especially visible because liquid
soft-fill then rendered empty strings.

## Acceptance Criteria

- [x] `.at[row, col] = value` writes to the store named by `coltype(col)` /
      colspecs when the column is registered.
- [x] Empty `output` index does not receive columns owned by `cache`.
- [x] `set_value` / `get_value_column` round-trip a dict on a cache column
      when output has no rows.
- [x] Regression test
      `test_at_setitem_routes_dict_to_cache_when_output_index_empty`.

## Implementation Notes

Route `__setitem__` through `coltype` first; only fall back to scanning `_d`
for an existing `(row, column)` cell. Do not invent columns on unrelated
empty frames.

## Related

- Referia CoE: `coe/2026-10-18_web-reviewer-skips-precompute-soft-fill.md`
- Referia backlog: `2026-10-18_web-reviewer-register-and-run-precompute`
- Code: `lynguine/assess/data.py` (`_AtAccessor.__setitem__`)
- Test: `lynguine/tests/test_assess_data.py::test_at_setitem_routes_dict_to_cache_when_output_index_empty`

## Progress Updates

### 2026-10-18

Root cause confirmed on Panel MPhil soft-fill (Candidate Email). Fix and
regression test landed on `main` working tree; smoke with WebReviewer yields
`Candidate Email` from PDF.

### 2026-10-18 (merged)

Merged via PR #42. Referia CoE
`2026-10-18_web-reviewer-skips-precompute-soft-fill` closed after operator
validation on Panel applications.
