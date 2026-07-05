---
id: "2026-07-05_finalize-data-missing-columns-before-compute"
title: "finalize_data runs compute before adding missing declared columns"
status: "Completed"
priority: "High"
created: "2026-07-05"
last_updated: "2026-07-05"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- yaml
- compute
- columns
---

# Task: finalize_data runs compute before adding missing declared columns

## Description

When reading data from YAML (or any sparse format where all-NaN columns are
absent), `finalize_data()` in `lynguine/access/io.py` attempted to run the
`compute` block before the schema declared in `columns` had been enforced.
If a `row_args` entry referenced a column that was absent from the loaded
DataFrame (because all its values were NaN and therefore not present in the
YAML records), a `KeyError` was raised.

The `_finalize_df()` method in `data.py` already correctly adds missing
declared columns as `None` — but it runs *after* `finalize_data()` has
already tried to execute `compute`. With Excel sources this never surfaced
because pandas materialises every column header even when all values are NaN.
YAML sources skip absent keys entirely, exposing the ordering bug.

**Concrete example**: In the `theses/examined/pdfpages/_referia.yml` config,
the `columns` list declares `suffix` and `preferred`. Both were all-NaN in
the source `candidates.xlsx`, so neither appears in any record of
`candidates.yml`. The `row_args` mapping `suffix: suffix` then caused
`KeyError: 'suffix'` during the `render_liquid` compute for the `Name` field.

## Acceptance Criteria

- [x] `finalize_data()` adds all columns declared in `columns` (as `None`)
      before running any `compute` block
- [x] Reading a YAML file with sparse columns and a `compute` block that
      references declared-but-absent columns no longer raises `KeyError`
- [x] Existing behaviour for Excel sources is unchanged
- [x] The fix mirrors the same logic already present in `_finalize_df()`

## Implementation Notes

Fix applied in `lynguine/access/io.py` in `finalize_data()`, immediately
before the `compute` block:

```python
# Add missing columns declared in "columns" before compute runs,
# so that row_args referencing sparse or all-NaN columns don't KeyError.
# (_finalize_df in data.py does the same, but runs after compute.)
if "columns" in interface:
    missing = [col for col in interface["columns"] if col not in df.columns]
    if missing:
        missing_df = pd.DataFrame({col: None for col in missing}, index=df.index)
        df = pd.concat([df, missing_df], axis=1)
```

Using `pd.concat` rather than per-column assignment avoids DataFrame
fragmentation warnings (consistent with the approach in `_finalize_df`).

Committed to lynguine `main` as:
`Fix: add missing declared columns before compute in finalize_data`
(commit 5b02de5)

## Related

- Discovered during Excel→YAML migration pilot (CIP-000A in referia repo)

## Progress Updates

### 2026-07-05

Bug identified, fix implemented and committed to lynguine main.
