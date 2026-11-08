---
id: "2026-11-06_cip0009-from-flow-wiring"
title: "CIP-0009: wire remote: into from_flow before read"
status: "Completed"
priority: "High"
created: "2026-11-06"
last_updated: "2026-11-06"
category: "features"
related_cips: ["0009"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-06_cip0009-materialise-helper"
tags:
- backlog
- features
- access
- assess
- cip0009
- remote
---

# Task: CIP-0009 wire remote: into from_flow

## Description

In `CustomDataFrame.from_flow`, call `materialise` before `data_exists` /
`read_data` when an item has `remote:`. Leave gsheet, CIP-0019 live plugins,
and local-only items on the current path. Failed fetches must raise and must
not create empty input frames.

## Acceptance Criteria

- [x] `from_flow` materialises before read when `remote:` is set
- [x] Items without `remote:` are unchanged
- [x] CIP-000F directory `source:` lists still work alongside `remote:`
- [x] Input fetch failure raises `ValueError` (no empty input frame)

## Related

- CIP: 0009

## Progress Updates

### 2026-11-06

Task created; depends on materialise helper.

### 2026-11-06

Implementation complete on worktree (from_flow wiring landed).
