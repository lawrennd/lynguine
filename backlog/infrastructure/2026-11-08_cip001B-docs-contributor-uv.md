---
id: "2026-11-08_cip001B-docs-contributor-uv"
title: "Update Sphinx metadata and contributor docs for uv"
status: "Completed"
priority: "Medium"
created: "2026-11-08"
last_updated: "2026-11-08"
category: "infrastructure"
related_cips: ["001B"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-08_cip001B-pep621-uv-lock"
tags:
- backlog
- documentation
- uv
- poetry
- sphinx
---

# Task: Update Sphinx metadata and contributor docs for uv

> Backlog tasks are DOING the work defined in CIPs (HOW).  
> Implements CIP-001B.

## Description

After packaging metadata moves to PEP 621, fix consumers of Poetry layout and rewrite contributor-facing install/test commands:

- `docs/conf.py` currently reads `pyproject['tool']['poetry']` for name/version/author — switch to `[project]`
- README / contributing docs that mention `poetry install` / `poetry run pytest`
- Inline install hints that still say `poetry install --extras …` (e.g. parquet message in `lynguine/access/io.py`)

Also smoke-check that `uv build` wheels still ship YAML data files and that extras import cleanly in a clean env (documents/parquet).

## Acceptance Criteria

- [x] Sphinx `docs/conf.py` resolves project/name/version/author from PEP 621 `[project]`
- [x] Docs HTML build succeeds with the updated conf (CI docs workflow or local `uv run sphinx-build`)
- [x] README and contributing docs describe uv (or plain pip) instead of Poetry as the supported contributor path
- [x] User-facing install hints no longer require Poetry wording for extras
- [x] `uv build` sdist/wheel install in a clean env; `import lynguine` works; extras bring in optional deps when requested

## Implementation Notes

`docs/conf.py` now uses stdlib `tomllib` (dropped the docs-group `toml` dependency). Wheel smoke-checked: defaults.yml and strategy YAMLs are present. Install-hint strings updated in `io.py`, `pdf.py`, `docx_reader.py`; parquet missing-extra test updated.

## Related

- CIP: 001B
- PRs: TBD
- Documentation: `docs/conf.py`, `README.md`, `docs/contributing/`

## Progress Updates

### 2026-11-08

Task created (Ready) after CIP-001B acceptance; blocked on packaging/lock conversion.

### 2026-11-08

Completed: conf/README/contributing + install hints; wheel contains YAML package data.
