---
author: "Neil D. Lawrence"
created: "2026-11-08"
id: "001B"
last_updated: "2026-11-08"
status: "In Progress"
compressed: false
effort: small
priority: medium
related_requirements: ["0001"]
related_cips: []
tags:
  - cip
  - packaging
  - tooling
  - uv
  - poetry
  - ci
  - maintainability
title: "Migrate developer packaging from Poetry to uv"
---

# CIP-001B: Migrate developer packaging from Poetry to uv

> CIPs describe HOW to achieve requirements (WHAT).  
> Implements [REQ-0001](../requirements/req0001_code-quality-maintainability.md) (maintainable dependency/tooling workflow).

## Status

- [x] Proposed - Initial idea documented
- [x] Accepted - Approved, ready to start work
- [x] In Progress - Actively being implemented
- [ ] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented
- [ ] Deferred - Postponed

## Summary

Replace Poetry as lynguine’s developer packaging tool with **uv**: PEP 621 `pyproject.toml`, `uv.lock`, and CI/docs that use `uv sync` / `uv run` / `uv build` instead of `poetry install` / `poetry run` / `poetry build`.

PyPI consumers who `pip install lynguine` are unaffected. Optional extras (`documents`, `parquet`), the `ndlconvert` console script, and docs/dev dependency groups remain.

## Motivation

Lynguine already uses a modern `pyproject.toml` + lockfile workflow, but the tooling surface is Poetry-specific:

- `[tool.poetry]` metadata (not PEP 621)
- `poetry.lock` + `poetry-core` build backend
- Three GitHub workflows install Poetry then wrap every step in `poetry run`
- Sphinx `docs/conf.py` reads `pyproject['tool']['poetry']` for name/version/author

uv is a fast, widely adopted installer/locker that prefers standard packaging metadata. Migrating reduces CI install time, aligns with PEP 621, and keeps one lockfile without requiring Poetry for day-to-day contribute / test / publish loops.

This is a **tooling** change, not a library API change. It supports REQ-0001’s maintainability outcome (predictable, current dependency tooling for contributors and CI).

## Detailed Description

### Current state

| Piece | Today |
|-------|--------|
| Metadata | `[tool.poetry]` + `[tool.poetry.dependencies]` |
| Extras | `[tool.poetry.extras]` → `documents`, `parquet` |
| Groups | `[tool.poetry.group.docs]`, `[tool.poetry.group.dev]` |
| Scripts | `[tool.poetry.scripts]` → `ndlconvert` |
| Build | `poetry-core` / `poetry.core.masonry.api` |
| Lock | `poetry.lock` |
| CI | `python-tests.yml`, `docs.yml`, `publish.yml` all Poetry |
| Docs metadata | `docs/conf.py` → `tool.poetry` |

### Target state

| Piece | After |
|-------|--------|
| Metadata | PEP 621 `[project]` (+ `[project.optional-dependencies]`) |
| Dev/docs deps | `[dependency-groups]` (`dev`, `docs`) — uv’s native groups |
| Scripts | `[project.scripts]` |
| Build | `hatchling` (or equivalent PEP 517 backend uv documents well) |
| Lock | `uv.lock` (commit); remove `poetry.lock` |
| CI | `astral-sh/setup-uv` + `uv sync --extra …` / `uv run` |
| Docs metadata | Read `[project]` (name, version, authors) |

### Design decisions

1. **Full migration, not dual tooling.** Drop Poetry as the supported contributor path. Do not keep `poetry.lock` alongside `uv.lock` long-term — one source of truth.

2. **Preserve install surface for library users.**
   - `pip install lynguine`
   - `pip install 'lynguine[documents]'` / `'lynguine[parquet]'`
   - Editable: `pip install -e ".[documents,parquet]"` still works via standard packaging; contributors may prefer `uv sync --extra documents --extra parquet --group dev`.

3. **Map Poetry groups/extras explicitly.**
   - Poetry extras → `[project.optional-dependencies]`
   - Poetry `docs` / `dev` groups → `[dependency-groups]` (optional; CI selects with `--group docs` / default sync includes `dev` as configured)

4. **Version and publish.** Keep release-tag ↔ package-version check. Prefer `uv build` + existing Trusted Publishing / token publish path; replace `poetry version -s` with reading `[project].version` (or `uv version` / equivalent once chosen at implementation).

5. **Sibling repos.** referia and others that consume lynguine via Poetry continue to work as PyPI/git dependencies. Migrating *those* repos is out of scope for this CIP.

6. **VibeSafe `.venv-vibesafe`.** Unrelated; leave the whats-next venv alone.

### Alternatives considered

| Approach | Why not (for this CIP) |
|----------|-------------------------|
| Keep Poetry; only add uv for CI cache speed | Two lock/tool stories for contributors |
| `uv pip install` against frozen `requirements.txt` only | Loses project extras/groups/scripts as first-class metadata |
| Defer until Poetry supports PEP 621 export only | Does not remove Poetry from CI/contributor path |

### Risks

- Publish workflow is the highest-blast-radius change; verify dry-run build + twine/uv check before cutting a release.
- `docs/conf.py` will break if metadata migration lands without updating the Sphinx reader.
- Wildcard Poetry deps (`"*"`) become concrete ranges or pinned loosely in PEP 621; lockfile still pins installs — review constraint wording when converting.

## Implementation Plan

1. **Convert `pyproject.toml`**
   - Move package metadata to `[project]`
   - Move runtime deps and optional extras
   - Move `dev` / `docs` to `[dependency-groups]`
   - Move `ndlconvert` to `[project.scripts]`
   - Set hatchling (or chosen) build backend and package includes (`defaults.yml`, strategy YAMLs)

2. **Lock and local verify**
   - `uv lock` → commit `uv.lock`
   - Remove `poetry.lock`
   - `uv sync --extra documents --extra parquet --group dev`
   - `uv run pytest`, `uv run ruff check lynguine`

3. **CI workflows**
   - `python-tests.yml`: setup-uv; sync with extras; `uv run` for ruff/pytest
   - `docs.yml`: sync with docs group; `uv run` sphinx / test_build
   - `publish.yml`: sync; version check; `uv build`; publish; drop Poetry install steps

4. **Docs and contributor text**
   - Update `docs/conf.py` for `[project]`
   - Update README / contributing docs that say `poetry install` / `poetry run pytest`
   - Soften or update inline hints that mention `poetry install --extras …` (e.g. parquet message in `lynguine/access/io.py`) to prefer `pip` / `uv` wording

5. **Smoke publish path**
   - Local `uv build` + artifact check (twine or uv)
   - Confirm wheel/sdist still includes YAML data files

## Backward Compatibility

- **Library API / on-disk schemas:** unchanged.
- **PyPI installers:** unchanged (`pip install lynguine` and extras).
- **Contributors:** must use uv (or plain pip against the PEP 621 project) instead of Poetry. Document the new commands in README.
- **Downstream Poetry projects:** still depend on published lynguine; no forced migration.

## Testing Strategy

- CI matrix (3.11, 3.13) green after workflow swap
- Docs workflow builds Sphinx successfully
- Local: tests + ruff under `uv run`
- Package: `uv build` produces sdist/wheel; install wheel in a clean env and import `lynguine`; confirm extras import paths (`pymupdf` / `pyarrow`) when installed with extras
- Publish job: version-tag check still fails closed on mismatch

## Related Requirements

- [REQ-0001](../requirements/req0001_code-quality-maintainability.md) — maintainable, current contributor and CI dependency workflow

## Implementation Status

Backlog (created 2026-11-08):

- [ ] [2026-11-08_cip001B-pep621-uv-lock](../backlog/infrastructure/2026-11-08_cip001B-pep621-uv-lock.md) — PEP 621 + `uv.lock`
- [ ] [2026-11-08_cip001B-ci-workflows-uv](../backlog/infrastructure/2026-11-08_cip001B-ci-workflows-uv.md) — CI/publish workflows
- [ ] [2026-11-08_cip001B-docs-contributor-uv](../backlog/infrastructure/2026-11-08_cip001B-docs-contributor-uv.md) — Sphinx conf + contributor docs + build smoke

Checklist:

- [ ] Convert `pyproject.toml` to PEP 621 + hatchling + dependency-groups
- [ ] Generate `uv.lock`; remove `poetry.lock`
- [ ] Update `python-tests.yml`, `docs.yml`, `publish.yml` for uv
- [ ] Update `docs/conf.py` and contributor-facing Poetry references
- [ ] Verify build artifacts and extras in a clean install

## References

- Current packaging: `pyproject.toml`, `poetry.lock`
- CI: `.github/workflows/python-tests.yml`, `docs.yml`, `publish.yml`
- Sphinx metadata: `docs/conf.py`
- [uv documentation — projects](https://docs.astral.sh/uv/concepts/projects/)
- [PEP 621 — project metadata](https://peps.python.org/pep-0621/)
