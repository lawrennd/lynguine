---
id: "2026-10-11_read-directory-relative-glob-double-join"
title: "read_directory double-joins relative directory with glob matches"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "bugs"
related_cips: ["000F"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- access
- directory
- glob
- cip000F
---

# Bug: `read_directory` double-joins relative directory with glob matches

## Description

In `lynguine/access/io.py` `read_directory`, after

```python
globname = os.path.join(directory, glob_text)
newfiles = glob.glob(globname)
```

matches are rejoined as `os.path.join(dirname, filename)` where `dirname` is the same `directory`. When `directory` is relative (no `allowed_roots` absolutisation), glob already returns paths like `catalog/item.yml`, and the rejoin becomes `catalog/catalog/item.yml`.

Discovered by baseline test `test_flat_glob_relative_directory` (CIP-000F prerequisite).

With `allowed_roots` set (typical `from_flow` path), `confine_configured_path` absolutises `directory` first, so `os.path.join` discards the prefix when the match is absolute — the bug is masked in jail-enabled flows.

## Acceptance Criteria

- [x] Glob matches are treated as full paths (no rejoin that duplicates the directory segment)
- [x] Relative `directory` without `allowed_roots` loads flat matches
- [x] Relative `directory` with `allowed_roots` still loads (no regression)
- [x] Absolute `directory` still loads (no regression)
- [x] Baseline xfail (if present) is removed or flipped to a passing assertion
- [x] Fix lands before or with CIP-000F recursive glob work (nested relative paths amplify the bug)

## Implementation Notes

- Prefer using `newfiles` from `glob.glob` directly as the file list (they already include the directory prefix), then confine each path
- `newdirs = [directory] * len(newfiles)` is only needed for the broken rejoin; `read_files` derives store_fields from the full path via `os.path.split`

## Related

- CIP: 000F
- Baseline: `2026-10-11_baseline-directory-glob-behaviour`
- Feature: `2026-10-11_recursive-directory-glob`

## Progress Updates

### 2026-10-11

Bug recorded from baseline directory-glob suite (`catalog/catalog/item.yml` FileNotFoundError).

Fixed in `read_directory`: use `glob.glob` matches as full paths and confine each directly (no `os.path.join(directory, match)`). Baseline relative test now passes; marked Completed.
