---
id: "2026-08-13_dependabot-gitpython"
title: "Harden GitPython dependency and clone usage (referia alerts #79–#99)"
status: "In Progress"
priority: "High"
created: "2026-08-13"
last_updated: "2026-10-04"
category: "infrastructure"
related_cips: []
owner: "lawrennd"
dependencies: []
tags:
- backlog
- security
- dependabot
- gitpython
- referia
---

# Task: Harden GitPython dependency and clone usage (referia alerts #79–#99)

## Description

GitPython is a **direct** lynguine dependency used in `lynguine/access/download.py`
(`Repo.clone_from`, `Repo.pull`). Referia consumes it transitively (`referia → lynguine → gitpython`).

Work has two layers:

1. **Version floor / lock** — keep lynguine (and then referia) on a patched GitPython.
2. **Trust boundary** — document or mitigate how clone URLs reach GitPython, independent of the pin.

### Current lynguine state (2026-10-04)

- `pyproject.toml`: `gitpython = ">=3.1.62"`
- `poetry.lock`: **3.1.62**
- Landed via [PR #28](https://github.com/lawrennd/lynguine/pull/28) (supersedes Dependabot [#27](https://github.com/lawrennd/lynguine/pull/27))
- Same lock refresh also bumped transitive `oauthlib` → 4.0.0 and `urllib3` → 2.8.0

### Version history

| When | Floor / lock | Scope |
|------|----------------|-------|
| 2026-08-13 | `>=3.1.58` / lock **3.1.59** | August advisories; referia alerts #79, #85–#99 needed ≥3.1.58 |
| 2026-10-04 | `>=3.1.62` / lock **3.1.62** | October GHSAs (e.g. GHSA-239g-whfq-7xj9, GHSA-g5vv-9gxw-82hx, GHSA-whh4-5q6c-9v3x, GHSA-59cr-6r3x-644w) |

Referia already completed the August refresh (lock **3.1.59**). It still needs a **second** lock
refresh to pick up lynguine’s `>=3.1.62` floor (referia lock remains **3.1.59** as of 2026-10-04).

Historical August alert table: `referia/backlog/infrastructure/2026-08-13_dependabot-gitpython.md`.

## Acceptance Criteria

- [x] `pyproject.toml` requires `gitpython >= 3.1.62`
- [x] `poetry.lock` at GitPython **3.1.62** (with oauthlib 4.0.0, urllib3 2.8.0)
- [x] Lynguine tests pass with the bumped lock (688 on Dependabot CI for #27; 687 package tests locally for #28)
- [ ] Review `lynguine/access/download.py` clone URL handling; document or mitigate untrusted URL risk
- [ ] Referia refreshes lock against lynguine `main` so GitPython resolves to **≥ 3.1.62** (second bump after August’s 3.1.59)
- [x] Cross-link October work on the referia companion backlog task (PR #28, new floor)

## Implementation Notes

### Version bump (done on lynguine)

```bash
# Edit pyproject.toml: gitpython = ">=3.1.62"
poetry update gitpython oauthlib urllib3
poetry run pytest
```

### Clone URL trust review (still open)

Review `_clone_or_pull_repo()` — `git.Repo.clone_from(self._git_url, ...)`.

**Current in-repo caller:** `lynguine/clone_or_pull.py` passes `git_url` from the **CLI**.
There is no validation or allowlist today.

**Forward-looking:** CIP-0009 plans config-driven remote access that may reuse `GitDownloader`
from interface/YAML; that would widen the trust boundary beyond CLI args.

Older advisory context for URL handling: GHSA-rwj8-pgh3-r573 (env expansion / clone URL).
Confirm whether untrusted URLs (or odd URL forms) can reach `clone_from`, and either document
“trusted operator / trusted config only” or add mitigations (scheme/host checks, reject odd forms).

### Referia follow-up (still open)

```bash
# In referia (after lynguine main has >=3.1.62)
poetry update lynguine gitpython
# Expect gitpython >= 3.1.62 in poetry.lock
```

Then update the referia companion task with PR #28 / floor notes and alert status.

## Related

- Referia backlog: `referia/backlog/infrastructure/2026-08-13_dependabot-gitpython.md`
- Code: `lynguine/access/download.py` (`GitDownloader`, ~290–311); CLI: `lynguine/clone_or_pull.py`
- Landed PR: https://github.com/lawrennd/lynguine/pull/28
- Superseded Dependabot PR: https://github.com/lawrennd/lynguine/pull/27
- Related design: CIP-0009 (config-driven remote access / materialise)
- No CIP solely for GitPython CVE remediation

## Progress Updates

### 2026-08-13

Task created. Lynguine lock already at 3.1.58; referia lock stale. Dependabot not enabled on lynguine repo.

### 2026-08-13 (implementation)

- `pyproject.toml`: `gitpython = ">=3.1.58"`
- `poetry.lock`: GitPython **3.1.59** after update
- Core tests pass (588/588 excluding pre-existing `test_server_mode.py` failures)
- Remaining at that time: referia August lock refresh; clone URL trust documentation

### 2026-10-04

- Dependabot opened group PR #27 (GitPython 3.1.62, oauthlib 4.0.0, urllib3 2.8.0)
- Follow-up [PR #28](https://github.com/lawrennd/lynguine/pull/28) landed: lock bump, floor `>=3.1.62`, Codecov soft-fail; #27 closed as superseded
- Package tests: 687 passed locally; CI green on #28
- Cross-linked referia companion task with PR #28 / 3.1.62 floor (referia task reopened to In Progress)
- Remaining: clone URL trust review; referia second lock refresh to ≥3.1.62
