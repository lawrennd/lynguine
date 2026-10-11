---
id: "2026-10-11_wide-flatten-wrapping-index"
title: "wide_flatten: wrapping index is singleton result label (Phase 3)"
status: "Ready"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-access-type"
tags:
- backlog
- features
- access
- wide-flatten
- index
- cip0010
---

# Task: wide_flatten wrapping index = singleton result label

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

CIP-0010 Phase 3 (Accepted): align `type: wide_flatten` with `stack` / `local`. Outer `index` names the **single wide row**. Tall identity used for flatten prefixes / `flattenKeys` comes from the nested `specifications` frame (nested `index` column/`set_index`, or index already set). Do not introduce `result_index`.

## Acceptance Criteria

- [ ] Outer `index` sets the wide row’s index label (e.g. `root`)
- [ ] Tall pre-flatten identity is taken from nested load (nested `index` / existing frame index), not from outer `index` as a column name
- [ ] Omit outer `index` → legacy behaviour (`0`); documented as deprecated for new configs
- [ ] No `result_index` key accepted or documented
- [ ] Existing callers that used outer `index` as tall column name are migrated in tests/docs to nested `index`

## Implementation Notes

- Primary touch: `read_wide_flatten` in `lynguine/access/io.py`
- After `wide_flatten_dataframe`, assign result index from `details.get("index")` when present
- Before flatten: if nested details include `index` as a column name, `set_index` there (or rely on nested finalize); do not use outer `index` for `set_index`
- Pair with tests/docs task `2026-10-11_wide-flatten-wrapping-index-tests-docs`

## Related

- CIP: 0010 (Phase 3)
- Requirement (via CIP): lynguine REQ-000C

## Progress Updates

### 2026-10-11

Task created (Ready) after Phase 3 Accepted and REQ-000C marked Ready.
