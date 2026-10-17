---
id: "2026-10-11_remove-legacy-manchester-cgi-scripts"
title: "Remove unused Manchester-era CGI / ndl* legacy scripts"
status: "Proposed"
priority: "Medium"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "infrastructure"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- legacy
- technical-debt
- cleanup
- ruff
---

# Task: Remove Unused Manchester-Era CGI Scripts

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).  
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Several top-level modules under `lynguine/` are personal Manchester CS CGI / diary tooling that predates the DOA package. They were brought into the tree as “old python scripts” and are not part of the modern lynguine surface.

Triggered by Ruff stage 1 (`2026-10-11_introduce-ruff-minimal-lint`): `lynguine/ndlcgi.py` is invalid Python 3 (syntax / indentation, Python 2 `print`, `cgi`/`cgitb`/`httplib`) and had to be `extend-exclude`d so CI could run. That file is not used by modern code.

**Confirmed unused by modern lynguine** (no imports from `config` / `access` / `assess` / `util` / tests; no Poetry entry points):

| File | Notes |
|------|--------|
| `lynguine/ndlcgi.py` | Broken Py3; only imported by sibling CGI scripts |
| `lynguine/ndlappointment.py` | CGI appointment editor; imports `ndlcgi` / `ndlcal` |
| `lynguine/ndlcal.py` | Hard-codes `/home/neil/mlprojects/...` paths |
| `lynguine/ndlexpenses.py` | CGI expenses helper; imports `ndlcgi` / `ndlcal` |
| `lynguine/ndlimage.py` | No external refs in package/tests |
| `lynguine/ndlmarkdown.py` | No external refs in package/tests |
| `lynguine/ndlstrutil.py` | No external refs in package/tests |
| `lynguine/ndltext.py` | No external refs in package/tests |
| `lynguine/old_data.py` | Superseded I/O helper; no external refs |

**Keep (not in scope):**

- `lynguine/ndlconvert.py` — active Poetry script entry point (`ndlconvert`)

Preferred outcome: **delete** the unused cluster from the package. If any script is still wanted personally, move it out of the published package (private archive / separate repo) rather than keeping it in lynguine.

## Acceptance Criteria

- [ ] Decision recorded: delete from package (preferred) vs move to a non-packaged archive location
- [ ] Unused Manchester CGI / `ndl*` modules listed above are removed from `lynguine/` (or relocated out of the installable package)
- [ ] `lynguine/ndlconvert.py` and its Poetry entry point remain
- [ ] No remaining imports or docs that treat the removed modules as part of lynguine’s API
- [ ] `pyproject.toml` Ruff `extend-exclude` for `lynguine/ndlcgi.py` is removed
- [ ] Tests still pass; Ruff check still passes under the current stage-1 config

## Implementation Notes

1. Grep once more for external consumers (`referia`, other repos) before deleting; in-tree evidence already shows no modern use.
2. Delete as one focused PR; avoid mixing with Ruff rule enablement.
3. After deletion, drop `extend-exclude = ["lynguine/ndlcgi.py"]` from `[tool.ruff]`.
4. Optional: if `docs/` source (not `_build`) mentions these scripts, update or remove those mentions.

## Related

- CIP: none
- Related backlog: `2026-10-11_introduce-ruff-minimal-lint` (Ruff exclude for `ndlcgi.py`)
- Related backlog: `2026-08-13_legacy-compute-py-cleanup` (similar legacy orphan cleanup)
- PRs: TBD
- Documentation: git history (“Add old python scripts”); `pyproject.toml` Ruff exclude

## Progress Updates

### 2026-10-11

Task created with Proposed status after Ruff stage 1 required excluding `ndlcgi.py`. Cluster confirmed unused by modern lynguine; only cross-refs are among the legacy CGI scripts themselves.
