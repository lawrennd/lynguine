---
id: "2026-08-13_dependabot-gitpython"
title: "Harden GitPython dependency and clone usage (referia alerts #79–#99)"
status: "In Progress"
priority: "High"
created: "2026-08-13"
last_updated: "2026-08-13"
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

Current lynguine state:

- `pyproject.toml`: `gitpython = ">=3.1.57"`
- `poetry.lock`: **3.1.58** (meets latest advisory patched version)
- Referia `poetry.lock` still resolves **3.1.51** (stale lock against git `main` lynguine)

Lynguine-side work: tighten the declared minimum, confirm safe usage of clone URLs, and ensure
consumers (referia) can refresh to ≥ 3.1.58.

**Note:** Dependabot alerts are **disabled** on the lynguine repository (see companion backlog task
`2026-08-13_enable-dependabot-security-alerts.md`).

## Dependabot alerts (via referia lock scan)

Patched version: **≥ 3.1.58**. Representative GHSAs: GHSA-rwj8-pgh3-r573 (clone URL env expansion),
GHSA-jm78-9fvv-mhgr, GHSA-wvpp-8hx9-p66j, GHSA-hmq2-w58f-27jc, and others (#85–#99).

Full list tracked in referia backlog:
`referia/backlog/infrastructure/2026-08-13_dependabot-gitpython.md`

## Acceptance Criteria

- [x] `pyproject.toml` requires `gitpython >= 3.1.58` (explicit, not only `>=3.1.57`)
- [x] `poetry.lock` remains at ≥ 3.1.58 after refresh (3.1.59)
- [ ] Review `lynguine/access/download.py` clone URL handling; document or mitigate untrusted URL risk
- [x] Lynguine tests pass (588 core; 51 pre-existing failures in `test_server_mode.py`)
- [ ] Referia can `poetry update gitpython` (or lynguine) and close alerts #79, #85–#99
- [ ] Cross-link completed work in referia backlog task

## Implementation Notes

```bash
# In lynguine
# Edit pyproject.toml: gitpython = ">=3.1.58"
poetry update gitpython
poetry run pytest
```

Review `_clone_or_pull_repo()` — `git.Repo.clone_from(self._git_url, ...)` is flagged in
GHSA-rwj8-pgh3-r573. Confirm `_git_url` sources (interface YAML) and whether URLs can contain
unexpanded env vars from untrusted input.

## Related

- Referia backlog: `referia/backlog/infrastructure/2026-08-13_dependabot-gitpython.md`
- Code: `lynguine/access/download.py` (lines ~290–309)
- No existing lynguine CIP covers GitPython CVE remediation.

## Progress Updates

### 2026-08-13

Task created. Lynguine lock already at 3.1.58; referia lock stale. Dependabot not enabled on lynguine repo.

### 2026-08-13 (implementation)

- `pyproject.toml`: `gitpython = ">=3.1.58"`
- `poetry.lock`: GitPython **3.1.59** after update
- Core tests pass (588/588 excluding pre-existing `test_server_mode.py` failures)
- Remaining: referia lock refresh; clone URL trust documentation
