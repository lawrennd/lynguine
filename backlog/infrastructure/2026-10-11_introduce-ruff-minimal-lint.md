---
id: "2026-10-11_introduce-ruff-minimal-lint"
title: "Introduce Ruff with a minimal lint/format config"
status: "In Progress"
priority: "Medium"
created: "2026-10-11"
last_updated: "2026-10-11"
category: "infrastructure"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- lint
- ruff
- tooling
- developer-experience
---

# Task: Introduce Ruff with a Minimal Config

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).  
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

Lynguine currently has almost no enforced Python lint or format tooling. The contributing style guide documents Black, but Black is not a Poetry dependency, there is no flake8/pylint/isort/mypy setup, and CI (`.github/workflows/python-tests.yml`) only runs pytest with coverage. The practical goal is to introduce Ruff as the first real lint/format tool, starting with a **minimal** configuration so adoption stays cheap and diffs stay small.

No CIP is required for this work: it is tooling/infrastructure, not an architectural change. Prefer one focused PR that adds Ruff, documents the minimal rule set, and optionally gates CI on that minimal check. Broader rule tightening and mass auto-fixes can follow in later tasks once the baseline is green.

## Acceptance Criteria

- [x] `ruff` is added as a Poetry development dependency
- [x] `pyproject.toml` has a minimal `[tool.ruff]` (and related) config: target Python 3.11, line length 88 (match the documented Black setting), `src` / package paths scoped to `lynguine` (and tests only if that stays quiet)
- [x] Default rule selection stays narrow at first (stage 1: `select = []`; enable `E4`/`E7`/`E9`/`F` in a follow-up once findings are handled)
- [x] `poetry run ruff check` succeeds on the scoped paths under the minimal config (stage 1: empty select; avoid a repo-wide style rewrite)
- [ ] `poetry run ruff format --check` succeeds on the scoped paths (deferred: ~75 files would reformat)
- [x] CI runs the same minimal Ruff check(s) on PRs/pushes to `main`
- [x] `docs/contributing/style_guide.rst` is updated to describe Ruff instead of Black
- [x] Short usage notes exist for contributors (commands to check and auto-fix locally)

## Implementation Notes

**Start minimal — suggested first config direction:**

```toml
[tool.ruff]
target-version = "py311"
line-length = 88
src = ["lynguine"]

[tool.ruff.lint]
# Keep the first cut narrow. Prefer defaults or a small select;
# expand rule families only after the baseline is green in CI.
ignore = []

[tool.ruff.format]
quote-style = "double"
```

**Suggested rollout order:**

1. Add the dependency and config only; run `ruff check` / `ruff format --check` locally and note violation volume.
2. If volume is high, narrow further (path excludes, temporary per-file ignores, or format-only first) rather than enabling more rules.
3. Wire CI once local check is green under the minimal config.
4. Update the style guide and contributing docs.
5. Defer aggressive rule expansion, import sorting campaigns, and mass `ruff format` of the whole tree to follow-up backlog items.

**Out of scope for this task:**

- Full Black→Ruff historical equivalence audits
- Enabling large rule sets (`ALL`, broad bugbear/complexity families) in the first PR
- Type checking (mypy/pyright) — separate concern
- Pre-commit hooks (optional follow-up)

## Related

- CIP: none (tooling task; CIP not required)
- PRs: TBD
- Documentation: `docs/contributing/style_guide.rst`, `docs/contributing/guide.rst`, `pyproject.toml`, `.github/workflows/python-tests.yml`

## Progress Updates

### 2026-10-11

Task created with Proposed status. Approach agreed: introduce Ruff without a CIP, start with a minimal config, and avoid a mass reformat in the first change.

### 2026-10-11 (stage 1)

In Progress. Stage 1 landed: Poetry `ruff` dev dependency, minimal `[tool.ruff]` config, CI `ruff check lynguine` step, style guide switched from Black to Ruff.

Baseline volume on `lynguine/` (why select stays empty):

- Classic `E4`/`E7`/`E9`/`F` ignoring `E501`: ~488 findings (~213 auto-fixable), including syntax errors in `lynguine/ndlcgi.py` (excluded via `extend-exclude` so empty-select CI can pass)
- Broader default/isolated runs: ~947 findings
- `ruff format --check`: ~75 files would reformat

Follow-ups: enable a narrow rule set and get it green; then add a format CI gate.
