---
id: "2026-11-06_cip0009-materialise-helper"
title: "CIP-0009: materialise() for remote url/github"
status: "Completed"
priority: "High"
created: "2026-11-06"
last_updated: "2026-11-06"
category: "features"
related_cips: ["0009"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- access
- download
- cip0009
- remote
---

# Task: CIP-0009 materialise() helper for remote url/github

## Description

Add `lynguine.access.download.materialise(item, interface)` that dispatches
`remote.type: url | github`, reuses FileDownloader / GitDownloader behaviour,
honours cache skip vs `refresh: true`, licence authorize, and path confinement
(CIP-000A). Reject unknown `remote.type` and legacy `source: {type: url|github}`
with a migration error pointing at `remote:`.

## Acceptance Criteria

- [x] `materialise` fetches URL to `directory`/`filename` when cache missing or refresh
- [x] `materialise` clones/pulls Git into `directory` when cache missing or refresh
- [x] Skip fetch when local artefact exists and `refresh` is not true
- [x] Unknown `remote.type` raises clear `ValueError`
- [x] Legacy remote-shaped `source:` raises migration error naming `remote:`
- [x] Existing FileDownloader / GitDownloader callers still work

## Implementation Notes

- Keep fetch URLs only from configuration, never from the data frame.
- Write only under the resolved confined `directory`.

## Related

- CIP: 0009

## Progress Updates

### 2026-11-06

Task created; CIP-0009 Accepted with `remote:` naming.

### 2026-11-06

Implementation complete on worktree (materialise helper landed).
