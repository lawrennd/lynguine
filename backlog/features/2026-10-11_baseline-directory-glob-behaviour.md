---
id: "2026-10-11_baseline-directory-glob-behaviour"
title: "Baseline tests for current directory-glob behaviour"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "features"
related_cips: ["000F"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- access
- directory
- glob
- testing
- cip000F
---

# Task: Baseline tests for current directory-glob behaviour

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Before implementing CIP-000F recursive globs and field projection, lock in today's directory-reader behaviour with real filesystem fixtures (not mocked `glob.glob`).

Existing suite coverage is thin: json/yaml/markdown round-trips use absolute `tmpdir` only; `test_read_directory` stubs `glob.glob`. Nested trees, relative directories, `**` without recursion, and `regexp` after expand are not pinned.

## Acceptance Criteria

- [x] Flat `*.yml` (or equivalent) under an absolute directory matches and loads
- [x] Flat match under a relative `directory` is exercised (document or fix join behaviour if broken)
- [x] Nested file is **not** matched by a flat glob when `recursive` is absent
- [x] `**` without `recursive: true` does not imply full-tree discovery (pin Python’s non-recursive `**` semantics)
- [x] `regexp` filters on basename after expand
- [x] `store_fields` populate directory / filename / root for a flat match
- [x] Tests live under `lynguine/tests/` and pass in the project test env

## Implementation Notes

- Prefer a focused module (e.g. `test_directory_glob_baseline.py`) or a clearly named section in `test_access_io.py`
- Use `tmp_path` fixtures; avoid mocking `glob.glob` for these cases
- If relative-directory rejoin (`os.path.join(directory, match)`) fails today, record it (xfail + bug task, or fix as a prerequisite before recursive work)
- CIP-000F recursive / `fields` tests build on this floor; do not implement those flags here

## Related

- CIP: 000F
- Unblocks: `2026-10-11_recursive-directory-glob`
- Documentation gap: `2026-10-11_document-recursive-directory-fields` (typed readers + non-recursive default)

## Progress Updates

### 2026-10-11

Task created (Ready) after survey of existing glob call sites and test/doc gaps.

Baseline suite added in `lynguine/tests/test_directory_glob_baseline.py`. Absolute flat glob, nested exclusion, `**` non-full-tree, `regexp`, `store_fields`, and relative+`allowed_roots` pass. Bare relative directory fails with double-join (`catalog/catalog/item.yml`) — documented as strict xfail and bug `2026-10-11_read-directory-relative-glob-double-join`. Marked Completed.
