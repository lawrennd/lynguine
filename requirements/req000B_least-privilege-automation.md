---
id: "000B"
title: "Least-Privilege Repository Automation"
status: "Implemented"
priority: "Medium"
created: "2026-08-19"
last_updated: "2026-08-19"
related_tenets:
- explicit-infrastructure
stakeholders:
- Maintainers
- Contributors
tags:
- requirement
- security
- ci
- github-actions
---

# REQ-000B: Least-Privilege Repository Automation

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

GitHub Actions jobs in this repository must run with the minimum `GITHUB_TOKEN` permissions they need, declared explicitly. A missing permissions block currently grants the default token (contents write on many repositories), which is more authority than tests or a docs build require.

CodeQL reports two medium `actions/missing-workflow-permissions` findings: `.github/workflows/python-tests.yml` and the docs **build** job in `.github/workflows/docs.yml`. The docs **deploy** job already declares `pages: write` and `id-token: write`.

**Why this matters**: Explicit infrastructure applies to automation as well as Python APIs. Token scope should be visible in the workflow, not inherited from GitHub defaults that change over time.

**Who benefits**: Maintainers reviewing workflows can see what a compromised action could do. Contributors copying these workflows do not inherit an overly broad token.

## Acceptance Criteria

- [x] Every workflow job has an explicit `permissions` block
- [x] Jobs that only checkout and test or build have no write access to repository contents
- [x] Jobs that deploy (GitHub Pages or similar) declare only the write scopes they use
- [ ] CodeQL `actions/missing-workflow-permissions` alerts for this repository are resolved

## Notes

This is a small outcome. It does not need a CIP; implementation is the backlog task `2026-08-19_least-privilege-github-actions`. It is a requirement so that future workflows (server tests, release jobs) are held to the same bar.

## References

- **Related Tenets**: `explicit-infrastructure`
- **CodeQL**: alerts 35 and 36
- **GitHub**: [permissions for `GITHUB_TOKEN`](https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs)

## Progress Updates

### 2026-08-19

Requirement proposed from CodeQL workflow-permissions alerts.

### 2026-08-19 (later)

Accepted. No CIP; tracked as backlog `2026-08-19_least-privilege-github-actions`. Status moved to In Progress.

### 2026-08-19 (implementation)

Workflows now declare per-job permissions. Tests: `contents: read`. Docs build: `contents: read` plus `actions: write` for `upload-pages-artifact`. Docs deploy unchanged (`pages: write`, `id-token: write`, no contents write). Status Implemented; CodeQL alerts 35 and 36 need a scan on the default branch to close.
