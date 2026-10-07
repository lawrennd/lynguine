---
id: "2026-10-07_hstack-repeated-rsuffix-collision"
title: "read_hstack MergeError when a third source recreates col_right"
status: "In Progress"
priority: "High"
created: "2026-10-07"
last_updated: "2026-10-07"
category: "bugs"
related_cips:
- "000E"
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- hstack
- join
- suffixes
---

# Task: read_hstack MergeError when a third source recreates col_right

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

`lynguine.access.io.read_hstack` joins multiple specifications with default `lsuffix=''` and `rsuffix='_right'`. A two-way join that shares a column (e.g. `crsid`) produces `crsid` and `crsid_right`. A third specification that also has `crsid` then tries to create `crsid_right` again. Recent pandas raises:

```
MergeError: Passing 'suffixes' which cause duplicate columns {'crsid_right'} is not allowed.
```

Seen on referia Queens students configs (`aims`, `dissertations`, `meetings`) where people input is hstacked with multiple Excel additionals that all carry `crsid`.

## Acceptance Criteria

- [x] Three-or-more-way `hstack` with a shared identity column does not raise `MergeError`
- [x] First occurrence of each overlapping column is kept; later colliding right columns are dropped (documented)
- [x] Existing two-way hstack suffix tests still pass (`B_right` behaviour unchanged)
- [x] Regression test for the three-way `crsid` case
- [ ] Behaviour reviewed and committed (temporary implementation in working tree)

## Implementation Notes

### Temporary implementation (working tree, 2026-10-06)

In `lynguine/access/io.py`:

- `_drop_join_suffix_collisions(left, right, lsuffix, rsuffix)` — before `DataFrame.join`, drop right columns whose `{col}{rsuffix}` already exists on left.
- `_drop_merge_suffix_collisions(...)` — same for the `on != 'index'` `pd.merge` path (skips the join keys).

Wired into `read_hstack` before join/merge. Regression: `lynguine/tests/test_access_io.py::test_read_hstack_drops_repeated_rsuffix_collisions`.

### Review before closing

- Confirm dropping the third identity column is preferable to unique incremental suffixes (`_right2`, …).
- Align policy language with `to_pandas` “earlier wins” (`2026-08-19_to-pandas-overlapping-columns`).

## Related

- CIP: [000E](../../cip/cip000E.md) (review required — do not treat provisional policy as Accepted)
- Backlog: `2026-08-19_to-pandas-overlapping-columns`
- Triggered by: `~/OneDrive/referia/supervision/queens_students/{aims,dissertations,meetings}`

## Progress Updates

### 2026-10-07

Task created to capture a provisional working-tree fix from a referia load-audit session. Linked to CIP-000E. Status In Progress until CIP review and commit.
