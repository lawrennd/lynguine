---
id: "2026-10-11_recursive-directory-glob"
title: "Thread recursive glob support through directory readers"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["000F"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-11_baseline-directory-glob-behaviour"
tags:
- backlog
- features
- access
- directory
- recursive
- cip000F
---

# Task: Thread recursive glob support through directory readers

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Implement CIP-000F recursive discovery: thread an opt-in `recursive` flag from each directory `source` entry (and optionally top-level `details`) into `read_directory`, so patterns such as `**/_referia.yml` match nested trees.

Default remains non-recursive so existing flat `yaml_directory` / sibling directory configs are unchanged. Path confinement (CIP-000A) must still apply to every matched path.

## Acceptance Criteria

- [x] `recursive: true` on a source entry enables recursive glob semantics (`glob.glob(..., recursive=True)` or equivalent `Path` API)
- [x] Absent / `recursive: false` preserves today's flat `glob.glob` behaviour
- [x] Nested fixture `a/b/c.yml` matches `**/c.yml` (or `**/*.yml`) only when `recursive: true`
- [x] Debug log records pattern, recursive flag, and match count
- [x] Paths outside `allowed_roots` still raise (CIP-000A regression)
- [x] `regexp` filter still applies after recursive expansion
- [x] No referia-specific ignore rules added; callers narrow via `glob` / `regexp`
- [x] Glob matches are used as full paths (no broken rejoin with relative `directory`)

## Implementation Notes

- Primary touch point: `lynguine/access/io.py` — `read_directory`
- Shared path: all directory readers benefit (`yaml_directory`, `json_directory`, `markdown_directory`, …)
- Precedence: source `recursive` wins, else `details["recursive"]`, else `false`
- Relative double-join fixed earlier (`2026-10-11_read-directory-relative-glob-double-join`)

## Related

- CIP: 000F
- Depends on: `2026-10-11_baseline-directory-glob-behaviour`
- Documentation: CIP-000F Configuration sketch / Behaviour table
- Downstream: referia CIP-0010 catalog allocation

## Progress Updates

### 2026-10-11

Task created (Ready) from Accepted CIP-000F implementation plan step 1.

Dependency on baseline directory-glob tests added; note about relative-path rejoin recorded.

Implemented: `glob.glob(..., recursive=...)` in `read_directory`; tests in `test_directory_glob_baseline.py`. Marked Completed.
