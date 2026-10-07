---
id: "2026-10-07_update-inherit-jail-security-test"
title: "Update stale inherit PathEscape test to match CIP-000E root extension"
status: "Completed"
priority: "High"
created: "2026-10-07"
last_updated: "2026-10-07"
category: "bugs"
related_cips:
  - "000E"
  - "000A"
owner: "Neil D. Lawrence"
dependencies: []
tags:
  - backlog
  - bug
  - tests
  - path-jail
  - inherit
  - coe
---

# Task: Update stale inherit PathEscape test to match CIP-000E root extension

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

CI run [37579504929](https://github.com/lawrennd/lynguine/actions/runs/37579504929) failed after CIP-000E (`4f68587`) because
`lynguine/tests/test_config_interface.py::test_from_file_inherit_cannot_leave_jail`
still expects `PathEscapeError` when inheriting `../outside`. CIP-000E intentionally
extends `allowed_roots` with explicit `inherit.directory` so sibling/ancestor parents
load under the path jail.

Spawned by CoE `coe/2026-10-07_stale-inherit-jail-test.md`.

Keep coverage that non-inherit escapes and `from_cwd_file` inherit outside CWD still
PathEscape (`test_from_file_rejects_parent_escape`,
`test_from_cwd_file_inherit_cannot_leave_cwd`).

## Acceptance Criteria

- [x] `test_from_file_inherit_cannot_leave_jail` updated (or renamed) so it asserts CIP-000E behaviour: inherit extends roots; load succeeds
- [x] Non-inherit parent-path escape and cwd-sandbox inherit escape tests still fail as intended
- [x] Updated test(s) pass locally

## Implementation Notes

Rewrite the assertion in `test_config_interface.py` to mirror
`test_from_file_inherit_allows_sibling_directory`: child loads parent via
`inherit.directory`, `parent_only` / child keys present, both directory realpaths in
`allowed_roots`. Prefer renaming to `test_from_file_inherit_extends_jail` so the name
matches the policy.

## Related

- CIP: 000E, 000A
- CoE: `coe/2026-10-07_stale-inherit-jail-test.md`
- CI: https://github.com/lawrennd/lynguine/actions/runs/37579504929
- Related backlog: `2026-10-07_inherit-extends-allowed-roots.md`

## Progress Updates

### 2026-10-07

Task created from CoE after CI failure diagnosis. Renamed
`test_from_file_inherit_cannot_leave_jail` → `test_from_file_inherit_extends_jail`
and asserted successful load with both directories in `allowed_roots`. Related escape
tests still pass. Status Completed.
