---
author: "Neil D. Lawrence"
created: "2026-08-19"
id: "000B"
last_updated: "2026-08-19"
status: "In Progress"
compressed: false
related_requirements: ["0004"]
related_cips: ["0005"]
tags:
- cip
- security
- logging
- credentials
- audit
title: "Make credential logging and audit storage actually secret-safe"
---

# CIP-000B: Make credential logging and audit storage actually secret-safe

> **Note**: CIPs describe HOW to achieve requirements (WHAT).
> Use `related_requirements` to link to the requirements this CIP implements.

## Status

- [x] Proposed - Initial idea documented
- [x] Accepted - Approved, ready to start work
- [x] In Progress - Actively being implemented
- [ ] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented (add reason, use superseded_by if replaced)
- [ ] Deferred - Postponed (use blocked_by field to indicate blocker)

## Summary

CIP-0005 added `SanitizingFormatter` and `get_secure_logger`, but the credential and access-control modules still log with the standard library logger, and the audit file writes unsanitized `credential_key` as JSON. Wire those call sites through an explicit, CodeQL-visible redaction helper so REQ-0004's "no secrets in logs" criterion holds for identifiers as well as values.

This CIP implements the remaining gap in [REQ-0004](../requirements/req0004_secure-credentials.md). It does not reopen CIP-0005 (closed); it is the follow-on that static analysis showed was still needed.

**Which requirements does this CIP address?** REQ-0004.

## Motivation

CodeQL reports 16 high `py/clear-text-logging-sensitive-data` alerts and 1 high `py/clear-text-storage-sensitive-data` alert. Almost all of them are the same pattern: a parameter named `key` / `credential_key` is interpolated into a log line or written to `audit.log`.

What is actually logged today:

| Alerts | Site | What is logged | Already sanitized? |
|--------|------|----------------|--------------------|
| 4, 5, 6 | `access_control.py` 198–209 | Audit line with `_sanitize_credential_key`; **and** raw `event_json` to file; **and** `print` of the line | Console/log line yes; **file no** |
| 7–11 | `access_control.py` 359–572 | Debug/warning with raw `credential_key` | No |
| 12–18 | `credentials.py` 480–664 | Debug/info/error with raw cache/manager `key` | No |
| 19 | `log.py` 38 | Generic `Logger.warning(message)` sink | No (taint funnel) |
| 3 | `access_control.py` 205 | `f.write(event_json)` | **Storage of unsanitized key** |

REQ-0004 and CIP-0005 claimed automatic sanitization. The sanitizer exists (`lynguine/security/secure_logging.py`) but is used by `migration.py` and tests, not by `credentials.py` or `access_control.py`. Those modules call `logging.getLogger(...)`.

CodeQL is also somewhat blunt: it treats **credential identifiers** as if they were **secret values**. Logging `google_sheets` is not the same as logging a token. Identifiers still leak structure (which secrets exist, naming schemes). The right outcome is: values never appear; identifiers appear only in a redacted or hashed form, including in the audit file.

Alert 19 (`lynguine/log.py`) is a library-wide sink: any `Logger.warning(message)` is treated as logging a password because `message` is an unsanitized parameter. Fixing that sink with the sanitizing formatter reduces false taint through the rest of the codebase.

## Detailed Description

### Identifier vs value

Introduce one explicit helper, used everywhere we currently interpolate a credential key:

```python
def redact_credential_identifier(key: str) -> str:
    """Return a log-safe form of a credential name, never the raw key."""
```

Keep the existing `_sanitize_credential_key` behaviour (short keys become `***`; longer keys become `abcd***wxyz`) or switch to a truncated SHA-256 hex digest. Prefer hashing if we want CodeQL to treat the result as sanitized; prefix/suffix redaction is nicer for operators but often still taints.

**Accepted decision:** hash credential identifiers for audit file and debug logs. Prefix/suffix redaction only if hashing still taints and we add a CodeQL sanitizer model. Do not log raw keys at any level.

Secret **values** continue to be handled by `SanitizingFormatter` pattern redaction. They must never be passed into log f-strings (today they mostly are not; the alerts are about keys).

### Wire secure logging as the default in security modules

- `credentials.py` and `access_control.py` use `get_secure_logger` (or `setup_secure_logging` on their loggers).
- Audit `log_event`:
  - Console/log message already uses `_sanitize_credential_key`; keep that, but source it from the shared helper.
  - `event.to_dict()` used for the JSON file must store `credential_key` in redacted/hashed form, not the raw key. If a forensic raw key is required, that is a separate, documented, off-by-default stream — not the default `~/.lynguine/audit.log`.
  - Drop or gate `print(f"[AUDIT] {log_msg}")`; stdout is not an audit sink.

### Default application logger

`lynguine.log.Logger` currently wraps `logging` with no sanitizer. Attach `SanitizingFormatter` in `basicConfig` / handler setup so generic warnings cannot reprint tokens that happen to appear in messages. That is the explicit default for a library that handles credentials; callers who want a raw formatter can pass one in.

### What we will not do

- `# noqa` / CodeQL suppression comments as the primary fix (hides the gap CIP-0005 left).
- Logging raw keys at DEBUG "because it is debug". Debug logs are the ones that get copied into issues.
- Treating CodeQL as wrong solely because the taint is a *name* not a *password*. Names are still sensitive in an audit sense.

### Alternatives considered

| Approach | Why not |
|----------|---------|
| Dismiss all 17 alerts as false positives | Audit file really does store clear-text keys; debug logs really do print them |
| Pattern-only sanitizer (existing formatter) | Does not redact `key=google_oauth` because it is not `password=...` |
| Rename variables so CodeQL stops matching | Does not change the leak; violates explicitness |

## Implementation Plan

1. **Shared `redact_credential_identifier`** in `secure_logging.py` with unit tests (empty, short, long, unicode).
2. **Audit JSON and log lines** use the helper; remove raw key from `to_dict()` default.
3. **Switch security modules** to `get_secure_logger`.
4. **Attach SanitizingFormatter** to `lynguine.log.Logger`.
5. **Re-run / wait for CodeQL**; add a modeled sanitizer only if hashing still taints.
6. **Update REQ-0004** acceptance notes; keep CIP-0005 closed.

## Backward Compatibility

- Log and audit line format changes: keys become redacted/hashed. Anyone grepping `audit.log` for a raw credential name will need the new form. Document that as an intentional break.
- `AuditEvent.credential_key` in memory can remain the raw key for access-control decisions; only serialization and logging change.
- No change to credential storage encryption or provider APIs.

## Testing Strategy

- Unit tests: identifier redaction; audit JSON has no raw key; formatter still redacts `password=` values
- Existing 41 credential tests still pass
- A test that a known key string does not appear in `audit.log` after `log_event`
- After merge, CodeQL alerts 3–19 should close or drop to a documented remainder

## Related Requirements

- [REQ-0004](../requirements/req0004_secure-credentials.md) — secure credential management (sanitization criterion not actually met)

## Implementation Status

- [x] Shared identifier redaction helper and tests
- [x] Audit file and log lines use helper
- [x] Security modules use secure logger
- [x] `lynguine.log.Logger` sanitizing formatter
- [ ] CodeQL re-check of alerts 3–19
- [ ] REQ-0004 status reconciled after verification

## References

- CodeQL alerts 3–19, rules `py/clear-text-logging-sensitive-data` and `py/clear-text-storage-sensitive-data`
- [CIP-0005](cip0005.md) (closed) — original credential system
- `lynguine/security/secure_logging.py` — sanitizer that is not on the default path

## Progress Updates

### 2026-08-19

Proposed from CodeQL alerts 3–19.

### 2026-08-19 (later)

Accepted. Credential identifiers are hashed in logs and the audit file; raw keys are not logged at any level.

### 2026-08-19 (implementation)

Started on branch `cip000B-credential-log-sanitization`: `redact_credential_identifier`, hashed audit JSON, secure loggers in credentials/access_control, sanitizing `lynguine.log.Logger`.
