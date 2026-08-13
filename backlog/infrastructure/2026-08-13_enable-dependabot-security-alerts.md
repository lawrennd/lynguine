---
id: "2026-08-13_enable-dependabot-security-alerts"
title: "Enable Dependabot security alerts on lynguine repository"
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
- github
---

# Task: Enable Dependabot security alerts on lynguine repository

## Description

The GitHub Dependabot alerts API returns **403: Dependabot alerts are disabled** for
`lawrennd/lynguine`. Referia has Dependabot enabled and surfaces lynguine transitive vulnerabilities
there, but lynguine itself has no native alert visibility.

Enabling Dependabot (alerts and/or version updates) on lynguine would:

- Surface GitPython, cryptography, and other dependency CVEs at the source
- Align with referia's security monitoring
- Reduce reliance on downstream consumers to report lynguine transitive issues

## Acceptance Criteria

- [x] Dependabot **security alerts** enabled for `lawrennd/lynguine`
- [ ] Optional: Dependabot **version updates** configured for `poetry.lock` / `pyproject.toml`
- [x] Confirm alerts API accessible: `gh api repos/lawrennd/lynguine/dependabot/alerts`
- [x] Document any alerts found and map to backlog tasks (starting with GitPython task)
- [ ] README or internal docs note where to check dependency security status

## Implementation Notes

Repository settings → Security → Dependabot → enable alerts.

Consider a minimal `.github/dependabot.yml` for weekly Poetry updates:

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
```

(Poetry projects often use `pip` ecosystem with `poetry.lock` in GitHub's Dependabot config.)

## Related

- Triggered by referia Dependabot triage (2026-08-13)
- Companion: `2026-08-13_dependabot-gitpython.md`

## Progress Updates

### 2026-08-13

Task created. Dependabot alerts confirmed disabled via GitHub API during referia alert summary.

### 2026-08-13 (later)

Dependabot alerts and security updates enabled on `lawrennd/lynguine`. API verified:
`hasVulnerabilityAlertsEnabled: true`. **24 open alerts** (mostly transitive dev/transitive deps):

| Package | Open alerts | Notes |
|---------|-------------|-------|
| pyasn1 | 5 | transitive (google-auth stack) |
| deepdiff | 4 | dev dependency |
| urllib3 | 4 | transitive |
| pytest | 2 | dev dependency |
| python-liquid | 2 | direct dependency |
| soupsieve | 2 | transitive |
| Pygments, httplib2, idna, protobuf, requests | 1 each | mixed |

**No native GitPython or cryptography alerts** — lynguine lock already at GitPython 3.1.58;
cryptography not resolved in lynguine lock. Original GitPython/cryptography backlog items remain
valid for referia transitive closure and declared minimums.
