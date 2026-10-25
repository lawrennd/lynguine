---
id: "2026-10-25_user-facing-docs-audit"
title: "Audit and repair user-facing documentation: stubs, overstated features, leftover ndlpy"
status: "In Progress"
priority: "High"
created: "2026-10-25"
last_updated: "2026-10-25"
category: "documentation"
related_cips:
- "0001"
- "0005"
- "0008"
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- documentation
- readme
- sphinx
- credentials
- honesty
---

# Task: Audit and repair user-facing documentation

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

User-facing docs (README + Sphinx Getting Started + Security + Server Mode) do not match how lynguine is actually used. Two problems noticed in reading, then confirmed by a fuller pass:

1. **Missing examples.** README promises a PMLR volume-1 BibTeX download/load/save walkthrough, then stops at `import lynguine`. Assess and Util "short examples" are the same empty stub. Sphinx `getting_started/examples.rst` is placeholder comments and points at a `docs/examples` directory that does not exist.
2. **Credentials overweight.** README leads with "enterprise-grade" credential management (encrypted storage, cloud vaults, RBAC, audit logging). The author has barely used this path. Security docs are ~2,600 lines; Getting Started is ~470 lines, most of it stubs. Cloud vaults are advertised but only environment-variable and encrypted-file providers exist.

CIP-0001 closed as if module docs and examples were done. Several Sphinx pages are still the ndlpy template. The completed task `2025-12-03_document-secure-credential-usage` is why credentials now dominate the front door.

This task is the inventory and the repair plan. Related work that should **not** be duplicated here:

- `2026-10-18_align-compute-framework-docs-vongole-intent` — compute inheritance / vongole
- `2026-10-17_document-segment-example-yaml` — CIP-0013 YAML sketches

## Findings (2026-10-25)

### A. Stub or missing examples

| Location | What it claims | What is there |
|---|---|---|
| `README.md` ~150–156 | Download PMLR v1 (Gaussian processes in practice), load it, save as BibTeX | `import lynguine` only |
| `README.md` ~163–167 | Assess short example | `import lynguine` only |
| `README.md` ~229–233 | Util short example | `import lynguine` only |
| `README.md` ~206–211 | Compute YAML shape | `function:` left empty |
| `docs/getting_started/examples.rst` | "Basic" and "Advanced" ndlpy examples | `# Code for the first example` |
| `docs/getting_started/examples.rst` | "More examples in `docs/examples`" | Directory does not exist |
| `examples/` | Runnable examples | Only `examples/server_mode/` |

The YAML format catalogue later in the README (csv/excel/json/yaml/bibtex/directory/wide_flatten) is real. The narrative walkthroughs at the top are not.

### B. Credentials and security docs vs actual surface

Shipped providers in `lynguine/security/credentials.py`: `EnvironmentCredentialProvider`, `EncryptedFileCredentialProvider`. No cloud-vault class. OS keychain is still a proposed backlog item (`2025-12-22_os-keychain-master-key-storage`).

Over-claims:

- README and `docs/security/index.rst`: "Multiple Backends — Environment variables, encrypted files, **or cloud vaults**"
- Same pages: "enterprise-grade", RBAC, rate limiting, GDPR / SOC2 / NIST checkmarks
- README Security section sits **above Installation**, so a first-time reader hits credentials before `pip install`
- Sphinx Security toctree includes `IMPLEMENTATION_SUMMARY.md` (~540 lines of CIP-era implementation dump) as user documentation
- Duplicate artifacts: `USER_GUIDE.md` / `user_guide.rst`, `IMPLEMENTATION_SUMMARY.md` / `implementation_summary.rst`, plus `SECURE_CREDENTIALS.md`

Line-count contrast (approximate):

| Area | Lines |
|---|---|
| Security (md + rst) | ~2,600 |
| Server mode | ~2,100 |
| `docs/compute_framework.md` | 1,383 |
| README | 984 |
| Getting Started (all rst) | ~470 |
| of which quickstart + examples + installation | ~78, and those are stubs |

### C. Leftover ndlpy / linguine naming

Sphinx still describes **ndlpy**:

- `docs/getting_started/quickstart.rst` — `import ndlpy`; `ndlpy.YourClass()`
- `docs/getting_started/examples.rst` — "use ndlpy effectively"
- `docs/getting_started/installation.rst` — "ndlpy can be installed"; `cd ndlpy`
- `docs/contributing/guide.rst` — ndlpy users, ndlpy Code of Conduct, ndlpy beginner issues

README mixes **Linguine** (the pasta/spec metaphor and `_linguine.yml`) with **lynguine** as if they were the same product. It also points at `https://github.com/lawrennd/linguine.git` as "the emerging linguine specification". Config keys such as `review` are documented as Linguine interface fields; that belongs in referia.

### D. Server mode documented as shipped product while CIP-0008 is Proposed

`docs/server_mode/` is a full manual (quickstart, migration, API, examples, troubleshooting) including a **156.3x speedup** claim. CIP-0008 status is still **Proposed**. Code exists (`lynguine/client.py`, `lynguine/server.py`), so this is the CIP-0005 pattern again: implementation and docs ran ahead of the CIP. User-facing docs should say experimental / not the default path, or the CIP should be accepted and closed honestly.

### E. README quality nits that fail a first read

- `%pip install lynguine` — Jupyter magic, not a shell install
- "The softare consists of TK principle parts."
- Codecov badge uses `YOUR_CODECOV_TOKEN`
- Access automodule blurb claims "databases"; there is no database access module in the toctree

### F. What is in better shape (do not redo)

These Sphinx pages look like real, post-CIP writing and should be kept as the model:

- `docs/getting_started/column_management.rst`
- `docs/getting_started/stacking.rst`
- `docs/getting_started/directory_sources.rst`
- README sections on directory readers, `wide_flatten`, and stacking (after the empty narrative stubs)

## Acceptance Criteria

- [x] README Access example either contains a working PMLR/BibTeX (or local BibTeX) walkthrough, or the promise is removed and replaced with a short example that actually runs
- [x] README Assess and Util stubs are filled or deleted
- [x] `docs/getting_started/quickstart.rst`, `examples.rst`, and `installation.rst` are lynguine (not ndlpy) and contain runnable snippets; no pointer to a missing `docs/examples`
- [ ] `docs/contributing/guide.rst` no longer refers to ndlpy
- [ ] README Security section is demoted: not above Installation; claims match shipped providers (env + encrypted file). "Cloud vaults", GDPR/SOC2 badges, and "enterprise-grade" marketing dropped or marked future
- [ ] Sphinx Security toctree is a short user page plus API; CIP implementation summaries are not presented as user guides
- [ ] Server mode docs are labelled to match CIP-0008 (Proposed / experimental) or CIP-0008 is accepted/closed to match the docs
- [ ] README install snippet is a real `pip`/`poetry` command; "TK principle parts" and the Codecov placeholder token are gone
- [ ] Linguine vs lynguine wording is consistent; referia-only keys (`review`) are not documented as lynguine interface fields

## Implementation Notes

Honesty over completeness. Prefer deleting a stub to leaving `import lynguine`. Prefer one working Getting Started path (install → a local YAML/`CustomDataFrame.from_flow` example → column/stacking links) over expanding credentials or server mode.

Suggested order:

1. Kill or fill empty examples (README + Getting Started) — this is what a reader hits first
2. Strip ndlpy leftovers
3. Demote credentials to a short "if you store Google Sheets / API secrets" page
4. Mark server mode experimental or align CIP-0008
5. README cleanup (install, typos, badge, Linguine/lynguine)

Do not fold vongole/compute-framework alignment into this task.

If the demotion of Security/Server Mode in `docs/index.rst` feels like a doc-architecture change rather than a repair, split that step into a small CIP. The stub/ndlpy/over-claim repairs do not need one.

## Related

- CIP: 0001 (closed documentation plan; stubs survived)
- CIP: 0005 (credentials; docs overshoot the shipped providers)
- CIP: 0008 (server mode still Proposed)
- Backlog: `2025-12-03_document-secure-credential-usage` (Completed — source of the overweight)
- Backlog: `2026-10-18_align-compute-framework-docs-vongole-intent` (leave alone)
- Backlog: `2025-12-22_os-keychain-master-key-storage` (future; must not be documented as present)

## Progress Updates

### 2026-10-25

Task created after a pass over README, `docs/getting_started/`, `docs/security/`, and `docs/server_mode/`. Trigger was the missing PMLR BibTeX example and the unused-feeling credentials coverage.

Accepted and started with empty examples on branch `docs-empty-examples`:

- README Access: local BibTeX write/read (`fake` → `write_bibtex` → `read_bibtex`). Download is described as cache-after-prompt, not a silent URL-to-table. PMLR remains the motivating case once a `.bib` is on disk.
- README Assess empty stub deleted; the existing `from_flow` and column examples stand.
- README compute YAML now uses registered `today`.
- README Util stub replaced with a `fake.to_bibtex` snippet.
- Sphinx `quickstart.rst` / `examples.rst` rewritten as lynguine; `installation.rst` no longer says ndlpy.
- Snippets run against conda `py311` (lynguine 0.1.2).

Still open: contributing ndlpy leftovers, credentials demotion, server-mode labelling, README install/typo/badge cleanup.
