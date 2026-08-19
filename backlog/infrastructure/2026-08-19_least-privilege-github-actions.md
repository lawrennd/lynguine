---
id: "2026-08-19_least-privilege-github-actions"
title: "Declare least-privilege GITHUB_TOKEN permissions on workflows"
status: "Completed"
priority: "Medium"
created: "2026-08-19"
last_updated: "2026-08-19"
category: "infrastructure"
related_cips: []
owner: "lawrennd"
dependencies: []
tags:
- backlog
- security
- ci
- github-actions
- codeql
---

# Task: Declare least-privilege GITHUB_TOKEN permissions on workflows

> No CIP: REQ-000B is small enough to implement directly.

## Description

`.github/workflows/python-tests.yml` and the docs **build** job in `.github/workflows/docs.yml` omit a `permissions` block, so they inherit the default `GITHUB_TOKEN` (often contents write). CodeQL alerts 35 and 36 (`actions/missing-workflow-permissions`) flag this.

The docs **deploy** job already declares `pages: write` and `id-token: write`. The build job still needs an explicit read-only (or artifact-upload) scope.

This task implements [REQ-000B](../../requirements/req000B_least-privilege-automation.md).

## Acceptance Criteria

- [x] `python-tests.yml` has an explicit `permissions` block (contents read is enough for checkout, tests, and Codecov upload via `CODECOV_TOKEN`)
- [x] Docs **build** job has an explicit `permissions` block; include `pages: write` only if `upload-pages-artifact` requires it, otherwise contents read plus whatever the action documents
- [x] Docs **deploy** job keeps its existing write scopes and does not gain contents write
- [ ] CodeQL alerts 35 and 36 close after the default branch scan
- [x] Future workflows copied from these files start from least privilege

## Implementation Notes

Per-job permissions (deploy already had its own block):

```yaml
# python-tests.yml build job
permissions:
  contents: read

# docs.yml build job
permissions:
  contents: read
  actions: write  # upload-pages-artifact (actions: none would block artifact upload)
```

Docs deploy is unchanged: `pages: write` and `id-token: write` only.

`upload-pages-artifact` does not require `pages: write` on the build job; that scope stays on deploy only.

## Related

- Requirement: [REQ-000B](../../requirements/req000B_least-privilege-automation.md)
- CodeQL: https://github.com/lawrennd/lynguine/security/code-scanning/35
- CodeQL: https://github.com/lawrennd/lynguine/security/code-scanning/36

## Progress Updates

### 2026-08-19

Task created at Ready after REQ-000B was accepted without a CIP.

### 2026-08-19 (later)

Implemented. Tests job is contents-read only. Docs build adds `actions: write` so the Pages artifact can upload. CodeQL closure waits for a scan after this reaches the default branch.
