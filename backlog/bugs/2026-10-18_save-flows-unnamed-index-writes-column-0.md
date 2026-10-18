---
id: "2026-10-18_save-flows-unnamed-index-writes-column-0"
title: "save_flows writes index as column 0 when index.name is None"
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
- CoE
- save_flows
- index
- csv
- panel
---

# Bug: Output CSV index column becomes `0` when `index.name` is unset

> Backlog tasks are DOING the work defined in CIPs / CoE follow-ups (HOW→DO).
> Spawned by CoE `coe/2026-10-18_save-flows-unnamed-index-column-0.md`.
>
> Discovered while loading Panel PhD preliminaries
> (`applications/panel/2026-27/phd/info/preliminary.csv`): config
> `output.index: Name` failed with missing column `"0"`.

## Description

`CustomDataFrame.save_flows` / `to_flow` materialise the index as a column
before `write_csv(..., index=False)`:

```python
pd.concat(
    [pd.Series(list(df.index), index=df.index, name=df.index.name), df],
    axis=1,
)
```

When `df.index.name` is `None`, pandas names that Series column the integer
`0`. The next load looks for `index: Name` and raises (referia web serve
503). Creating a new output frame with `pd.DataFrame(index=cdf.index, ...)`
can leave `index.name` unset even when the YAML specifies `index: Name`.

## Acceptance Criteria

- [x] `save_flows` / `to_flow` write a named index column from
      `df.index.name` or, if unset, from `details['index']`.
- [x] Never write a column whose name is the integer `0` for this reason.
- [x] Creating a missing output frame in `from_flow` sets `index.name`
      from the flow's `index` field.
- [x] Regression test covers unnamed index + `interface[typ]['index']`.

## Implementation Notes

Helper `_resolve_index_column_name` / `_dataframe_for_output_write` on
`CustomDataFrame`. Panel CSVs already renamed `0` → `Name` as a data
workaround; code fix prevents recurrence on Save.

## Related

- CoE: `coe/2026-10-18_save-flows-unnamed-index-column-0.md`
- Panel PhD/MPhil `preliminary.csv` load failure (referia apps)

## Progress Updates

### 2026-10-18

Task created from CoE after Panel PhD load diagnosis. Fixed in
`lynguine/assess/data.py` with regression tests in
`test_set_value_d_sync.py`. CoE closed.
