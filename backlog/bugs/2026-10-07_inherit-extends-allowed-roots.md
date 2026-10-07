---
id: "2026-10-07_inherit-extends-allowed-roots"
title: "Inherit loads fail PathEscape when parent directory is outside child jail"
status: "In Progress"
priority: "High"
created: "2026-10-07"
last_updated: "2026-10-07"
category: "bugs"
related_cips:
- "000A"
- "000D"
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- inherit
- path-jail
- allowed_roots
---

# Task: Inherit loads fail PathEscape when parent directory is outside child jail

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

CIP-000A confines configured paths to `allowed_roots` (default: the config directory). Child interfaces that `inherit.directory` a sibling or ancestor (e.g. `../institutions/`, `../../../people/`) then fail with `PathEscapeError` when loading the parent YAML or when reading inherited data sources, because those paths sit outside the child’s directory root.

CIP-000A allows the caller to pass a wider `allowed_roots` list; inherit is a first-class, trusted config mechanism and should extend the jail to include the inherit directory (and union the parent’s roots into the child) without requiring `unbounded_paths=True`.

**Security constraint:** YAML contents must not enlarge the jail arbitrarily. Only the explicit `inherit.directory` (and the parent interface’s already-confined roots) should be added. HTTP/`SessionManager` must not default to unbounded (CIP-000D).

## Acceptance Criteria

- [x] Loading a child that inherits a sibling/ancestor directory under the same review tree does not PathEscape solely because the parent dir ≠ child dir
- [x] Child `allowed_roots` includes the inherit directory and unions parent roots after parent load
- [x] `unbounded_paths=True` and `cwd_sandbox` inherit paths remain as before
- [x] Unit coverage for inherit root extension
- [ ] Reviewed against CIP-000A/D (no YAML-driven root enlargement; HTTP default still jailed)
- [ ] Committed after review

## Implementation Notes

### Temporary implementation (working tree, 2026-10-06)

In `lynguine/config/interface.py` when constructing the parent for inherit (non-unbounded, non-cwd_sandbox):

1. Build `parent_roots = list(self.allowed_roots or [])` and append `realpath(inherit_directory)` if missing.
2. Call `from_file(..., allowed_roots=parent_roots, unbounded_paths=False)`.
3. After load, append each root from `self._parent.allowed_roots` into `self.allowed_roots` if missing.

Test coverage in `lynguine/tests/test_access_paths.py` (inherit roots).

### What this does *not* fix

Paths outside the review tree that appear only inside YAML (`$HOME/private/...`, `$HOME/mlatcl/...`) still PathEscape under a jailed caller. That is intentional. Trusted local helpers may pass `unbounded_paths=True`; HTTP/`WebReviewer` must not. Operator-supplied roots at process/server start are the supported way to widen the jail for those data homes.

## Related

- CIP: 000A (path jail), 000D (CodeQL / HTTP vs local entry points)
- Referia: keep `WebReviewer` jailed; `referia.data.Data` / `display.Scorer` may opt out for Jupyter

## Progress Updates

### 2026-10-07

Task created to capture a provisional working-tree fix from a referia load-audit session. Status In Progress until CIP-aligned review and commit.
