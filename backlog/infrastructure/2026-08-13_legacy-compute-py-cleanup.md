---
id: "2026-08-13_legacy-compute-py-cleanup"
title: "Resolve legacy lynguine/compute.py orphaned module"
status: "Proposed"
priority: "Low"
created: "2026-08-13"
last_updated: "2026-08-13"
category: "infrastructure"
related_cips: ["0007"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- legacy
- technical-debt
- compute
- codeql
---

# Task: Resolve legacy lynguine/compute.py orphaned module

## Description

`lynguine/compute.py` is a legacy, orphaned module that predates (or duplicates) the current
compute implementation in `lynguine/assess/compute.py`.

Evidence:

- Added in commit `e9ad35d` with **invalid import syntax** (`import .log`, etc.) from the outset
- **Not imported** anywhere in the codebase or exported from `lynguine/__init__.py`
- Active `Compute` class lives in `lynguine/assess/compute.py` (690+ lines, tested, documented)
- CodeQL failed to parse the file until syntax was patched (2026-08-13, commit `e753539`)
- Runtime issues remain even after syntax fix:
  - References `settings.Settings` (no such class; `Interface` is used in assess/compute)
  - Uses `pd`, `self._data`, `otherdf` without imports or initialization
  - `comptypes` defined as method but accessed as property (`self.comptypes`)

CIP-0007 discusses future vongole migration and assess-level compute stubs; this top-level file
is not part of that plan and creates confusion about where compute logic lives.

## Acceptance Criteria

- [ ] Decision recorded: **delete**, **redirect stub**, or **revive and align** with assess/compute
- [ ] If deleted: confirm no external consumers (PyPI installs, referia, docs links)
- [ ] If stub: document deprecation and re-export from `lynguine/assess/compute.py`
- [ ] If revived: full alignment with assess/compute API, tests, and imports
- [ ] CodeQL / CI no longer flags the file (automatic if deleted or made valid)
- [ ] CIP-0007 or docs updated if compute module layout changes

## Implementation Notes

**Recommended default: delete** — nothing references the file; assess/compute is canonical.

Before deletion:

```bash
# Confirm no references
rg 'lynguine\.compute|from lynguine import compute' .
rg 'from \.compute import|import compute' lynguine/
```

If retaining for historical reasons, replace with a minimal deprecation stub:

```python
"""Deprecated: use lynguine.assess.compute.Compute."""
import warnings
from lynguine.assess.compute import Compute

warnings.warn(
    "lynguine.compute is deprecated; use lynguine.assess.compute",
    DeprecationWarning,
    stacklevel=2,
)
__all__ = ["Compute"]
```

## Related

- Code: `lynguine/compute.py` (legacy), `lynguine/assess/compute.py` (canonical)
- CIP: [CIP-0007](../../cip/cip0007.md) — vongole/compute migration plans
- Fix: commit `e753539` — CodeQL parse error (import syntax only)
- Docs: `docs/compute_framework.md`

## Progress Updates

### 2026-08-13

Task created after CodeQL reported parse failure on `lynguine/compute.py`. Syntax patched in
`e753539`; file remains legacy/orphaned with unresolved runtime defects.
