---
id: "2026-10-11_wide-flatten-tests"
title: "Unit and integration tests for wide_flatten"
status: "Ready"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["0010"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_wide-flatten-core-helper"
- "2026-10-11_wide-flatten-access-type"
tags:
- backlog
- features
- testing
- wide-flatten
- cip0010
---

# Task: Unit and integration tests for wide_flatten

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Lock CIP-0010 behaviour with focused tests: helper edge cases plus one integration path through `read_data` / `type: wide_flatten` (nested multi-row source → one wide row).

Core-helper unit tests may land with the helper task; this task owns completeness and the access-path integration coverage.

## Acceptance Criteria

- [ ] Unit: happy path, both `order` values, `columns` subset
- [ ] Unit: duplicate index error, empty frame, `str` coercion of non-string names
- [ ] Unit or doc-assert: separator-in-index policy
- [ ] Integration: nested in-memory or `yaml_directory` (CIP-000F-style) under `wide_flatten` → assert column set and values
- [ ] Integration: nested `compute` field appears before widen; optional outer `compute` on wide row (thin finalize only)
- [ ] Tests under `lynguine/tests/` pass in the project test env

## Implementation Notes

- Prefer `tmp_path` for any directory fixture; avoid mocking the helper away in the integration test
- Soft dependency on CIP-000F readers already in tree; in-memory nested `type: local` is enough if simpler

## Related

- CIP: 0010
- Depends on: core helper + access type tasks

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-0010 — test step.
