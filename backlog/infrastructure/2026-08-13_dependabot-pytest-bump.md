---
id: "2026-08-13_dependabot-pytest-bump"
title: "Upgrade pytest dev dependency for tmpdir CVE (alerts #11, #24)"
status: "Completed"
priority: "Medium"
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
- pytest
- dev-dependencies
---

# Task: Upgrade pytest dev dependency for tmpdir CVE (alerts #11, #24)

## Description

Lynguine Dependabot reports **2 open pytest alerts** (#11, #24), both **medium** severity:
**GHSA-6w46-j5rx-g56g** — vulnerable tmpdir handling. Patched in **≥ 9.0.3**.

Current lynguine state:

- `pyproject.toml`: `pytest = "^6.2.5"` (dev dependency)
- `poetry.lock`: **6.2.5**
- Related dev plugins: `pytest-cov ^3.0.0`, `pytest-mock ^3.3.1`

This is a **major version bump** (6.x → 9.x). Expect plugin compatibility checks and possible
test-suite adjustments (deprecated APIs, tmpdir/`tmp_path` usage, warning filters).

## Acceptance Criteria

- [x] `pyproject.toml` requires `pytest >= 9.0.3` (or `^9.0.3`)
- [x] `pytest-cov` and `pytest-mock` versions compatible with pytest 9.x
- [x] `poetry.lock` refreshed; Dependabot alerts #11 and #24 closable
- [x] Full test suite passes (or pre-existing failures documented separately)
- [x] CI workflow (`.github/workflows/python-tests.yml`) unchanged or updated if needed

## Implementation Notes

```bash
# In lynguine
# Edit pyproject.toml dev-dependencies, e.g.:
#   pytest = "^9.0.3"
#   pytest-cov = "^6.0.0"   # verify latest compatible
#   pytest-mock = "^3.14.0" # verify latest compatible
poetry update pytest pytest-cov pytest-mock
poetry run pytest lynguine/tests/ -q
```

Check for:

- Deprecated `pytest` APIs removed in 7.x–9.x
- Tests using legacy `tmpdir` fixture → migrate to `tmp_path` where needed
- Increased deprecation warnings from older plugins
- Whether `test_server_mode.py` failures pre-date this bump (51 known failures as of 2026-08-13)

## Related

- Companion: `2026-08-13_enable-dependabot-security-alerts.md` (alert triage table)
- CI: `.github/workflows/python-tests.yml`
- Dependabot alerts #11, #24 (lynguine repo)

## Progress Updates

### 2026-08-13

Task created. Pytest bump deferred during initial Dependabot remediation (GitPython, cryptography,
transitive lock refresh). Native lynguine alerts: 2 medium pytest tmpdir issues.

### 2026-08-13 (implementation)

- `pyproject.toml`: `pytest ^9.0.3`, `pytest-cov ^6.0.0`, `pytest-mock ^3.14.0`
- `poetry.lock`: pytest **9.1.1**, pytest-cov **6.3.0**, pytest-mock **3.15.1**
- Core suite: **595 passed** (excluding pre-existing `test_server_mode.py` failures)
- CI workflow unchanged (`poetry install` + `pytest`)
- Follow-up (optional): migrate legacy `tmpdir` fixtures to `tmp_path` in test files
