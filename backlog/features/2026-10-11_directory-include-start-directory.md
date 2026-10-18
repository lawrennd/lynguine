---
id: "2026-10-11_directory-include-start-directory"
title: "Directory sources can omit matches in the start directory (descendants only)"
status: "Completed"
priority: "High"
created: "2026-10-11"
last_updated: "2026-10-18"
category: "features"
related_cips: ["000F"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- directory
- yaml_directory
- recursive
- discovery
---

# Task: Directory sources can omit matches in the start directory (descendants only)

> Linked CIP: 000F (recursive directory + field projection).
> Consumer: referia CIP-0010 root overview — discover nested `_referia.yml` without listing the overview file in `.` itself.

## Description

When a directory source uses `directory: .` with `recursive: true` and `glob: "**/_referia.yml"`, matches include the file in the start directory. Overview configs that live in that directory need an explicit, generic option to list **only descendants** (files under child directories), not matches whose parent is the source directory itself.

## Acceptance Criteria

- [x] Source (and/or details) accepts `include_start_directory` (bool), default `true` (current behaviour)
- [x] When `false`, paths whose immediate parent directory is the source `directory` are omitted; nested matches remain
- [x] Works for recursive and non-recursive globs consistently
- [x] Documented in Directory-of-Files docs alongside `recursive` / `fields`
- [x] Unit tests: start-dir file excluded; nested file kept; default unchanged

## Implementation Notes

- Implement in shared `read_directory` path so all `*_directory` readers benefit (same as CIP-000F).
- Compare resolved absolute paths; do not special-case `_referia.yml`.
- Name bikeshed alternative: `descendants_only: true` — prefer `include_start_directory: false` for positive default matching today.

## Related

- CIP: 000F
- referia CIP-0010 (overview discovery)
- PRs: (none yet)

## Progress Updates

### 2026-10-11

Task created (Proposed) from referia overview design: exclude overview directory’s own config by listing subdirectories only.

### 2026-10-11 (later)

Marked Ready — unblocks referia tall-first overviews (`inline_list` + `yaml_directory` without listing the overview file itself).

### 2026-10-11 (implemented)

Implemented in `read_directory`: source/details `include_start_directory` (default `true`); `false` drops matches whose parent is the source directory. README Directory of Files updated; unit tests added.
