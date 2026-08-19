---
id: "2026-08-19_least-privilege-github-actions"
title: "Declare least-privilege GITHUB_TOKEN permissions on workflows"
status: "Ready"
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

- [ ] `python-tests.yml` has an explicit `permissions` block (contents read is enough for checkout, tests, and Codecov upload via `CODECOV_TOKEN`)
- [ ] Docs **build** job has an explicit `permissions` block; include `pages: write` only if `upload-pages-artifact` requires it, otherwise contents read plus whatever the action documents
- [ ] Docs **deploy** job keeps its existing write scopes and does not gain contents write
- [ ] CodeQL alerts 35 and 36 close after the default branch scan
- [ ] Future workflows copied from these files start from least privilege

## Implementation Notes

Minimal starting point from CodeQL:

```yaml
permissions:
  contents: read
```

Place it at workflow level or per job. Per-job is clearer when deploy needs extra scopes.

`actions/upload-pages-artifact` may need `pages: write` on the **build** job; check the action docs when implementing. Do not give the test job write access to contents.

## Related

- Requirement: [REQ-000B](../../requirements/req000B_least-privilege-automation.md)
- CodeQL: https://github.com/lawrennd/lynguine/security/code-scanning/35
- CodeQL: https://github.com/lawrennd/lynguine/security/code-scanning/36

## Progress Updates

### 2026-08-19

Task created at Ready after REQ-000B was accepted without a CIP.
