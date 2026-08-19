---
id: "2026-08-19_sphinx-generation-ci-gate"
title: "Make Sphinx documentation generation fail CI on real errors"
status: "Proposed"
priority: "Medium"
created: "2026-08-19"
last_updated: "2026-08-19"
category: "documentation"
related_cips: ["0001"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- documentation
- sphinx
- autodoc
- ci
---

# Task: Make Sphinx documentation generation fail CI on real errors

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

CIP-0001 already chose Sphinx, autodoc, and the module RST layout. The Documentation workflow on [PR #21](https://github.com/lawrennd/lynguine/pull/21) was green, but generation is not healthy: the test harness swallows failures, and the build emits errors and broken references.

`docs/test_build.py` is written as a script that `return`s an exit code. Pytest therefore never fails `test_sphinx_build` (`PytestReturnNotNoneWarning`). `-W` (treat warnings as errors) is commented out so the build can “succeed with warnings.”

The docs job on that PR still produced:

- autodoc error: unexpected indentation in the `Interface` docstring
- missing `docs/_static` (`html_static_path` warning)
- RST title underlines too short on module pages and `docs/index.rst`
- toctree points at a non-existent `improvement_plan`
- broken cross-references (`compute_framework`, `data_frame.md`, `SECURITY.md`, …)
- `compute_framework.md` and `SECURE_CREDENTIALS.md` are not in any toctree

This is repair of CIP-0001’s build, not a new documentation architecture. Keep it off the BibTeX fake-data bug; that is `2026-08-19_flaky-bibtex-fake-generation`.

## Acceptance Criteria

- [ ] `test_sphinx_build` asserts success (does not `return` an exit code)
- [ ] Sphinx is run so real errors fail CI; restore `-W` once the existing warnings are cleared, or fail on error-level messages until then
- [ ] `docs/_static` exists or is removed from `html_static_path`
- [ ] RST title underlines match title length
- [ ] `docs/index.rst` toctree targets exist, or the dangling `improvement_plan` entry is removed
- [ ] Broken MyST/Sphinx cross-references listed above are fixed or removed
- [ ] Orphan docs (`compute_framework.md`, `SECURE_CREDENTIALS.md`) are in a toctree or explicitly excluded
- [ ] `Interface` docstring (and any other autodoc indentation errors) parse as RST

## Implementation Notes

Do not change the docs system (still Sphinx + autodoc + RTD theme). The HOW is CIP-0001.

Order of work:

1. Fix content (RST underlines, docstring, missing files, toctrees, refs) so a clean build is possible.
2. Change `docs/test_build.py` to `assert` / `pytest.fail` on non-zero `sphinx-build`.
3. Re-enable `-W` if the remaining warnings are gone; otherwise keep warnings visible but fail on ERROR.

Adding autodoc pages for `security` and `log` is optional follow-up, not required to close this task.

## Related

- CIP: 0001
- PR that surfaced it: [#21](https://github.com/lawrennd/lynguine/pull/21)
- Test: `docs/test_build.py`
- Workflow: `.github/workflows/docs.yml`
- Config: `docs/conf.py`, `docs/index.rst`

## Progress Updates

### 2026-08-19

Task created after PR #21 docs CI passed while Sphinx still reported generation errors. Separate from the flaky BibTeX fixture.
