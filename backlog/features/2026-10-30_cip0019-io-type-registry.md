---
id: "2026-10-30_cip0019-io-type-registry"
title: "CIP-0019 register_io_type, dispatch, plugins, entry points"
status: "Completed"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
category: "features"
related_cips: ["0019"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- access
- io
- plugins
- cip0019
---

# Task: CIP-0019 register_io_type, dispatch, plugins, entry points

> Tabular IO registry so live stores (Trello, IMAP, …) live in separate packages. This task ships the hook, not those packages.

## Description

Add `lynguine.access.io_types` with `register_io_type` / `get_io_type` /
`list_io_types`. Consult the registry from `read_data` / `write_data`
before raising on an unknown `type:`. Import interface `plugins:` in
`from_flow`. Optionally lazy-load `lynguine.io_types` entry points by
type name. Builtin elifs stay in v1. Writes require a registered writer
and `write: true`.

## Acceptance Criteria

- [x] Reserved builtin names cannot be registered
- [x] In-test registration is enough for `read_data` to return a DataFrame
- [x] Read-only write raises and does not write a file
- [x] `plugins:` import success and named failure
- [x] Entry-point stub loads by type name only
- [x] Builtin `csv` / `fake` behaviour unchanged
- [x] No network; no Trello/Gmail credentials

## Implementation Notes

- Home: `lynguine/access/io_types.py`, re-exported from `io.py`.
- Test-local `memtable` registration; do not add a new builtin type.
- Worktree: `/Users/neil/lawrennd/lynguine-cip0019` on `cip0019-pluggable-io-types`.

## Related

- CIP: 0019
- Requirement: REQ-0010

## Progress Updates

### 2026-10-30

Task created after CIP-0019 was accepted for implementation on a
separate worktree.

Implemented. `test_io_types.py` and `test_access_io.py` passed
(168 tests).
