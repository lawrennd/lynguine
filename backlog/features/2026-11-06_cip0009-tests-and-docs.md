---
id: "2026-11-06_cip0009-tests-and-docs"
title: "CIP-0009: tests and Access docs for remote:"
status: "Completed"
priority: "High"
created: "2026-11-06"
last_updated: "2026-11-06"
category: "features"
related_cips: ["0009"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-06_cip0009-from-flow-wiring"
tags:
- backlog
- features
- access
- documentation
- cip0009
- remote
---

# Task: CIP-0009 tests and Access docs

## Description

Extend download tests for dispatch, cache skip, refresh, unknown type,
HTTP/Git errors, no implicit URL-from-filename, and CIP-000F coexistence.
Add a `from_flow` integration test with mocked network. Document `remote:`
in the README Access section; contrast with CIP-0019 live `type:` and note
gsheet remains a reader.

## Acceptance Criteria

- [x] Unit tests cover cache skip, refresh, errors, legacy source migration
- [x] Integration: mocked fetch then `from_flow` / `read_data` of cached file
- [x] No live internet in CI
- [x] README Access shows `remote:` example

## Related

- CIP: 0009

## Progress Updates

### 2026-11-06

Task created.

### 2026-11-06

Implementation complete on worktree (tests and README landed).
