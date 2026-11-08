---
id: "2026-11-08_cip001B-ci-workflows-uv"
title: "Migrate GitHub Actions workflows from Poetry to uv"
status: "Ready"
priority: "High"
created: "2026-11-08"
last_updated: "2026-11-08"
category: "infrastructure"
related_cips: ["001B"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-08_cip001B-pep621-uv-lock"
tags:
- backlog
- ci
- github-actions
- uv
- poetry
---

# Task: Migrate GitHub Actions workflows from Poetry to uv

> Backlog tasks are DOING the work defined in CIPs (HOW).  
> Implements CIP-001B.

## Description

Update the three Poetry-based workflows so CI and release use uv:

- `.github/workflows/python-tests.yml`
- `.github/workflows/docs.yml`
- `.github/workflows/publish.yml`

Replace Poetry install/`poetry run`/`poetry build`/`poetry publish` with `astral-sh/setup-uv` (or equivalent), `uv sync`, `uv run`, `uv build`, and an updated publish/version-check path.

## Acceptance Criteria

- [ ] `python-tests.yml` installs with uv (extras documents+parquet), runs ruff and pytest via `uv run`
- [ ] Matrix still covers Python 3.11 and 3.13; Codecov upload behaviour preserved
- [ ] `docs.yml` syncs the docs group and builds Sphinx via `uv run`
- [ ] `publish.yml` version-vs-tag check works without Poetry; package builds with `uv build`
- [ ] Publish still reaches PyPI (token or Trusted Publishing as currently configured)
- [ ] No workflow step depends on `pip install poetry` / `poetry …`

## Implementation Notes

Depends on the PEP 621 + `uv.lock` task so sync has a lockfile and standard metadata.

For publish: keep the fail-closed tag/version mismatch check; read version from `[project].version` or uv’s version command. Prefer verifying `uv build` artifacts (and twine/uv check) before relying on a real release.

## Related

- CIP: 001B
- PRs: TBD
- Documentation: `.github/workflows/python-tests.yml`, `docs.yml`, `publish.yml`

## Progress Updates

### 2026-11-08

Task created (Ready) after CIP-001B acceptance; blocked on packaging/lock conversion.
