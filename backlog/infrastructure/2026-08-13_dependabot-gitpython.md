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

Referia's Dependabot scan reports **15 open GitPython alerts** (#79, #85–#99), all transitive via
`lynguine → gitpython`. Lynguine declares GitPython directly and uses it in
`lynguine/access/download.py` (`Repo.clone_from`, `Repo.pull`).

Current lynguine state (2026-10-04):

- `pyproject.toml`: `gitpython = ">=3.1.62"`
- `poetry.lock`: **3.1.62** (covers GHSA-239g-whfq-7xj9, GHSA-g5vv-9gxw-82hx, GHSA-whh4-5q6c-9v3x, GHSA-59cr-6r3x-644w)
- Companion Dependabot group PR also bumps transitive `oauthlib` → 4.0.0 and `urllib3` → 2.8.0

Lynguine-side work: tighten the declared minimum, confirm safe usage of clone URLs, and ensure
consumers (referia) can refresh to ≥ 3.1.62.

## Dependabot alerts (lynguine, 2026-10-04)

Patched version for current open GitPython alerts: **≥ 3.1.62**. Earlier August referia list
targeted ≥ 3.1.58; that floor is now superseded.

Also closed by the same lock refresh (transitive):

- `urllib3` ≥ 2.8.0 (alerts #27–#29)
- `oauthlib` ≥ 4.0.0 (alerts #25–#26)

Full historical referia list:
`referia/backlog/infrastructure/2026-08-13_dependabot-gitpython.md`

## Acceptance Criteria

- [x] `pyproject.toml` requires `gitpython >= 3.1.62`
- [x] `poetry.lock` at GitPython **3.1.62** (with oauthlib 4.0.0, urllib3 2.8.0)
- [ ] Review `lynguine/access/download.py` clone URL handling; document or mitigate untrusted URL risk
- [x] Lynguine tests pass with the bumped lock (688 passed on Dependabot CI)
- [ ] Referia can `poetry update gitpython` (or lynguine) and close remaining consumer alerts
- [ ] Cross-link completed work in referia backlog task

## Implementation Notes

```bash
# In lynguine
# Edit pyproject.toml: gitpython = ">=3.1.62"
poetry update gitpython oauthlib urllib3
poetry run pytest
```

Review `_clone_or_pull_repo()` — `git.Repo.clone_from(self._git_url, ...)` is flagged in
GHSA-rwj8-pgh3-r573. Confirm `_git_url` sources (interface YAML) and whether URLs can contain
unexpanded env vars from untrusted input.

## Related

- Referia backlog: `referia/backlog/infrastructure/2026-08-13_dependabot-gitpython.md`
- Code: `lynguine/access/download.py` (lines ~290–309)
- Dependabot PR: https://github.com/lawrennd/lynguine/pull/27
- No existing lynguine CIP covers GitPython CVE remediation.

## Progress Updates

### 2026-08-13

Task created. Lynguine lock already at 3.1.58; referia lock stale. Dependabot not enabled on lynguine repo.

### 2026-08-13 (implementation)

- `pyproject.toml`: `gitpython = ">=3.1.58"`
- `poetry.lock`: GitPython **3.1.59** after update
- Core tests pass (588/588 excluding pre-existing `test_server_mode.py` failures)
- Remaining: referia lock refresh; clone URL trust documentation

### 2026-10-04

- Dependabot opened group PR #27 for GitPython 3.1.62, oauthlib 4.0.0, urllib3 2.8.0 (closes 9 alerts)
- Raised declared floor to `gitpython >= 3.1.62`
- Codecov upload no longer fails the Python Tests job when the token is unavailable (Dependabot CI)
- Remaining: clone URL trust review; referia consumer lock refresh
