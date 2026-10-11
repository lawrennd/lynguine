---
id: "2026-10-11_wide-flatten-wrapping-index-tests-docs"
title: "Tests and docs for wide_flatten wrapping index (Phase 3)"
status: "Ready"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "documentation"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-wrapping-index"
tags:
- backlog
- documentation
- tests
- wide-flatten
- index
- cip0010
---

# Task: Tests and docs for wide_flatten wrapping index

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Lock CIP-0010 Phase 3 behaviour with tests and user-facing docs: outer `index` is the singleton label; tall key is nested; legacy omit → `0`.

## Acceptance Criteria

- [ ] Unit/integration tests cover named outer `index`, nested tall index, and omit → `0`
- [ ] Tests that previously passed outer `index` as a tall column name are updated
- [ ] README `wide_flatten` section documents new semantics and migration
- [ ] Acceptance check script (if any) updated for Phase 3
- [ ] CIP-0010 Phase 3 checklist items can be marked done after this lands

## Implementation Notes

- `lynguine/tests/test_wide_flatten.py`
- README wide_flatten section
- `scripts/check_cip0010_wide_flatten.py` if still asserting old index behaviour

## Related

- CIP: 0010 (Phase 3)
- Depends on: `2026-10-11_wide-flatten-wrapping-index`

## Progress Updates

### 2026-10-11

Task created (Ready) after Phase 3 Accepted.
