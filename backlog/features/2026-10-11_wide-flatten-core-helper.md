---
id: "2026-10-11_wide-flatten-core-helper"
title: "Implement wide_flatten helper (unstack + joined column names)"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- access
- reshape
- wide-flatten
- cip0010
---

# Task: Implement wide_flatten helper (unstack + joined column names)

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Implement CIP-0010’s pure reshape helper: turn a multi-row DataFrame with a unique index into a **single-row** frame whose column names are `{index}{separator}{field}` (or field-then-index per `order`).

No YAML / `read_data` wiring in this task — keep the helper testable on in-memory frames.

## Acceptance Criteria

- [x] Helper accepts `separator`, `order` (`index_then_field` | `field_then_index`), optional `columns` subset
- [x] Happy path: N×M → 1×(N×M) with correct names and values
- [x] Non-unique index raises a clear error
- [x] Empty-frame behaviour documented and tested (pick one: one empty row vs empty columns)
- [x] Index / column values coerced with `str(...)` in the join
- [x] Separator-in-index policy for v1: document “must not appear in index strings” (or implement cheap escape if trivial)
- [x] Optional `columns` drops other value columns (document; no silent globals unless explicitly chosen)
- [x] Unit tests without filesystem

## Implementation Notes

- `wide_flatten_dataframe` in `lynguine/access/io.py`
- Empty frame → one empty row, no value columns
- Separator in index labels → `ValueError` (v1)

## Related

- CIP: 0010
- Unblocks: `2026-10-11_wide-flatten-access-type`

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-0010 — core helper step.

Implemented `wide_flatten_dataframe`; unit coverage in `test_wide_flatten.py`. Marked Completed.
