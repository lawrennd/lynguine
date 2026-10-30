---
id: "2026-10-30_output-write-duplicate-index-column"
title: "output write prepends index column even when explode already kept it"
status: "Proposed"
priority: "Medium"
created: "2026-10-30"
last_updated: "2026-10-30"
category: "bugs"
related_cips:
- "0014"
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- save_flows
- index
- explode
- yaml
- pandas
---

# Bug: `_dataframe_for_output_write` duplicates the identity column

> Backlog tasks are DOING the work defined in CIPs / CoE follow-ups (HOW→DO).
> Follow-up to `backlog/bugs/2026-10-18_save-flows-unnamed-index-writes-column-0.md`.
> Surfaced by CIP-0014 explode on referia `07_grounds` Save
> (`dialogue-analysis/ai-dialogue-formats/07_grounds/`).

## Description

On Save, pandas warns:

```
UserWarning: DataFrame columns are not unique, some columns will be omitted.
  data_dict = df.to_dict("records")
```

at `lynguine/access/io.py` `write_yaml` (line ~808). The file is still
correct: the omitted copy is the same identity values. The warning is
the invariant failing, not data loss.

Two layers both materialise the identity field as a column:

1. **In memory** (`_finalize_df`): identity is the **index**, not a
   column. Load drops `unit_id` / `phrase_id` from columns.
2. **On disk** (`_dataframe_for_output_write`): YAML/CSV writers ignore
   the index (`to_dict("records")`, `index=False`), so Save concatenates
   a Series of index values onto the frame as a named column.

The 2026-10-18 helper named that Series so an unnamed index would not
become pandas column `0`. It always concatenates. It never asks whether
the column is already there.

**CIP-0014 explode** then builds a write-shaped tall table and does
`set_index(index, drop=False)`. That is deliberate: the child key
(`phrase_id`) is listed in `output.columns`, pack/merge still need it as
a column, and the index is only there to enforce uniqueness. The
exploded frame already looks like a YAML record table.

Save then concatenates `phrase_id` again. Pandas warns and keeps the
first copy. A second warning on the same Save is the cache write through
the same helper (`_grounds_cache.yml.gz`).

Do not “fix” this in referia YAML. Listing `phrase_id` under
`output.columns` is correct. Do not switch explode to `drop=True`: the
tall frame is supposed to carry identity as a column.

Triggering config: `07_grounds` output explode of `grounds` with
`index: phrase_id`. Same helper will fire on any explode-to-yaml/csv
Save (extract `phrases.yml`, and so on).

## Acceptance Criteria

- [ ] `_dataframe_for_output_write` emits the identity column **once**
- [ ] Explode `set_index(..., drop=False)` plus Save does not warn, and
      YAML records still contain the index field
- [ ] The 2026-10-18 unnamed-index case still writes `Name` not `0`
      (`test_set_value_d_sync.py`)
- [ ] Regression: explode tall frame with identity already a column;
      written frame has unique columns and matching index values
- [ ] Do not filter `UserWarning` or drop duplicate names after concat

## Implementation Notes

The owner is `_dataframe_for_output_write` on `CustomDataFrame`
(`lynguine/assess/data.py`). It should be the **inverse of
`_finalize_df`**: identity appears as a column once. Drop it if it is
already a column, then prepend from the index.

Proposed (not applied):

```python
def _dataframe_for_output_write(self, df, details=None):
    """Build a write frame with a named index column (never pandas ``0``)."""
    index_name = self._resolve_index_column_name(df, details)
    work = df.copy()
    if work.index.name is None:
        work.index.name = index_name
    if index_name in work.columns:
        work = work.drop(columns=[index_name])
    return pd.concat(
        [
            pd.Series(list(work.index), index=work.index, name=index_name),
            work,
        ],
        axis=1,
    )
```

What not to do:

- Silence the pandas `UserWarning`
- `df.loc[:, ~df.columns.duplicated()]` after concat (hides the clash)
- Change `explode_list_field` to `drop=True`
- Remove `phrase_id` from referia `output.columns`

Existing tests to keep green: `TestSaveFlowsIndexColumnName` in
`lynguine/tests/test_set_value_d_sync.py`. New coverage belongs next to
the CIP-0014 explode write path (`test_explode_pack_flow.py` or
`test_set_value_d_sync.py`).

## Related

- Backlog: `2026-10-18_save-flows-unnamed-index-writes-column-0`
  (Completed; named the concat Series, did not invert `_finalize_df`)
- CIP: 0014 (explode `drop=False` is the in-tree caller that surfaces it)
- Referia: `07_grounds` Save of `grounds.yml` / `_grounds_cache.yml.gz`

## Progress Updates

### 2026-10-30

Task created after referia `07_grounds` Classify-all Save. Diagnosis:
`write_yaml` → `to_dict("records")` on a frame with duplicate
`phrase_id` from explode `drop=False` plus `_dataframe_for_output_write`
concat. Proposed inverse-of-finalize helper recorded above; not
applied. Lynguine working tree was on `cip0017-slidespdf-extract`; this
task lands on `main` only.
