---
id: "2026-08-13_dependabot-cryptography-transitive"
title: "Track cryptography transitive CVE (referia alert #93)"
status: "In Progress"
priority: "Medium"
created: "2026-08-13"
last_updated: "2026-08-13"
category: "infrastructure"
related_cips: ["0005"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- security
- dependabot
- cryptography
- google-auth
---

# Task: Track cryptography transitive CVE (referia alert #93)

## Description

Referia Dependabot alert **#93** (high): **CVE-2026-69247** / GHSA-g6cj-pr64-35w5 — PKCS#7
Bleichenbacher oracle in `cryptography` 44.x–49.x; patched in **≥ 50.0.0**.

In referia's lock, `cryptography` is transitive via:

`lynguine → google-api-python-client → google-auth → cryptography`

Lynguine does **not** declare `cryptography` directly in `pyproject.toml`. The optional
`google-auth` extras pull `cryptography (>=38.0.3)`. CIP-0005 implemented lynguine's credential
security module with optional `cryptography` for encrypted storage.

## Acceptance Criteria

- [x] Confirm whether lynguine runtime/install paths require `cryptography` (credential encryption, Google APIs)
- [x] If required: add explicit `cryptography = ">=50.0.0"` to `pyproject.toml` (or document consumer responsibility)
- [x] Refresh `poetry.lock` and verify compatibility with CIP-0005 credential code
- [ ] Referia alert #93 closable after consumer lock refresh
- [x] CIP-0005 compatibility notes updated if minimum cryptography version changes

## Implementation Notes

Lynguine's own lock may not currently resolve `cryptography` until google-auth extras are installed.
Referia's full install does resolve it (49.0.0 today).

Evaluate whether to:

1. Add `cryptography` as a direct optional dependency under a `security` group, or
2. Rely on referia/consumers to pin `cryptography >= 50`, with lynguine documenting the minimum

Run CIP-0005 credential tests after any bump (PBKDF2HMAC compatibility was previously an issue at 45.x).

**Decision (2026-08-13):** Added direct `cryptography = ">=50.0.0"` to main dependencies so
consumer lockfiles inherit the patched minimum (not optional group only).

## Related

- CIP: [CIP-0005](../../cip/cip0005.md) — Secure credential management
- Referia backlog: `referia/backlog/infrastructure/2026-08-13_dependabot-cryptography-jupyterlab.md`
- Dependabot alert #93 (referia repo)

## Progress Updates

### 2026-08-13

Task created from referia Dependabot triage. No lynguine-native Dependabot alerts (alerts disabled on repo).

### 2026-08-13 (implementation)

- `pyproject.toml`: direct `cryptography = ">=50.0.0"`
- `poetry.lock`: cryptography **50.0.0**
- CIP-0005 credential tests: **41/41 passed** with cryptography 50.0.0
- Updated `lynguine/security/README.md` and CIP-0005 compatibility notes
- Remaining: referia `poetry update` to pick up lynguine constraint and close alert #93
