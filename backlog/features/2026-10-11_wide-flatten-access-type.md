---
id: "2026-10-11_wide-flatten-access-type"
title: "Wire type: wide_flatten through read_data like series/hstack"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-core-helper"
tags:
- backlog
- features
- access
- reshape
- wide-flatten
- cip0010
---

# Task: Wire type: wide_flatten through read_data like series/hstack

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Expose CIP-0010 as access `type: wide_flatten`: load nested `specifications` via `read_data`, apply the wide-flatten helper, return through `finalize_data` so outer `compute:` can run on the single wide row.

## Acceptance Criteria

- [x] `read_data` accepts `type: wide_flatten`
- [x] Nested `specifications` loaded with `read_data` (same pattern as `read_series`)
- [x] Details keys: `separator` (default `_`), `order` (default `index_then_field`), optional `columns`
- [x] Debug log records op name, separator, order, input row count, output column count
- [x] Nested `compute:` still runs on the multi-row frame (via nested `finalize_data`)
- [x] Outer `compute:` on the `wide_flatten` details runs on the wide row (via outer `finalize_data`)
- [x] Missing / wrong `type` and missing `specifications` raise clear errors
- [x] No change to `stack` / `hstack` / `vstack` / `series` semantics

## Implementation Notes

- `read_wide_flatten` + `read_data` branch in `lynguine/access/io.py`
- Optional `index` column to `set_index` before flatten
- Wide row uses a trivial `RangeIndex`

## Related

- CIP: 0010
- Depends on: `2026-10-11_wide-flatten-core-helper`
- Related: CIP-0011 (phase honesty; out of scope for this task)

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-0010 — access wiring step.

Implemented and covered by `test_read_wide_flatten_*`. Marked Completed.
