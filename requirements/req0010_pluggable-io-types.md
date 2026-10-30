---
id: "0010"
title: "Third-party tabular IO types without growing lynguine"
status: "Proposed"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
related_tenets:
- explicit-infrastructure
- flow-based-processing
stakeholders:
- Application developers (referia, lamd, catalog flows)
- Plugin authors (Trello, mail, SQL, and similar live stores)
- Lynguine maintainers
tags:
- requirement
- access
- io
- plugins
- architecture
---

# REQ-0010: Third-party tabular IO types without growing lynguine

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

A flow can name a tabular `type` that lynguine itself does not implement (Trello boards, IMAP/Gmail message lists, SQL queries, and similar live stores). That type still participates in the same access path as `excel` / `csv` / `yaml`: `read_data` (and, when the type allows it, `write_data`) returns or accepts a DataFrame that `finalize_data` and the rest of the flow can use.

Lynguine remains thin. Vendor SDKs, OAuth clients, and host-specific schemas live outside the core package. Unknown types fail with a clear error that names the type and the registered types. No silent fallback, and no inference of a live store from a URL-shaped filename.

This outcome is for **tables** (one row per card, message, ticket, query result). Structured **documents** (PDF, DOCX, Google Docs bodies) remain REQ-000D / CIP-0013.

**Why this matters**: *Explicit infrastructure* — `type:` is the named contract; plugins do not hide behind auto-detect. *Flow-based processing* — live stores are accessed during flow, not at construction, and they produce the same store shape as file readers.

**Who benefits**: referia (and other apps) that want allocation/input from Trello or mail subjects without forking `io.py`; maintainers who must not absorb every vendor SDK into lynguine; plugin authors who need a stable registration contract.

## Acceptance Criteria

- [ ] A flow can declare `type:` for a tabular source that is not a lynguine builtin and still receive a DataFrame through `read_data`
- [ ] Builtin types (`excel`, `csv`, `yaml`, `gsheet`, directory types, …) keep today's behaviour
- [ ] Adding a new live-store type does not require editing lynguine's `read_data` / `write_data` dispatch or adding that vendor as a lynguine dependency
- [ ] Types that do not implement write fail clearly on `write_data` rather than writing a file-shaped fallback
- [ ] Unknown `type` values raise with the requested name and the list of registered types
- [ ] Credentials for live stores use the existing credential system (REQ-0004 / CIP-0005); secrets do not appear in interface YAML
- [ ] Document-shaped sources (PDF/DOCX/Google Docs text) are not satisfied by this requirement; they remain REQ-000D

## Notes

CIP-0009 already treats Google Sheets as a **reader** (`type: gsheet`), not a `source:` fetch, and defers SQL as a live reader rather than a file download. This requirement is the outcome those live readers need: a way to exist without each one becoming a core elif branch.

Zero-plugin proof path remains valid: export Trello/mail to YAML or CSV and use builtins. Plugins are for when the live store is the authoritative input.

## References

- Tenet: [explicit-infrastructure](../tenets/lynguine/explicit-infrastructure.md)
- Tenet: [flow-based-processing](../tenets/lynguine/flow-based-processing.md)
- Related: [REQ-0002](./req0002_predictable-architecture.md), [REQ-0004](./req0004_secure-credentials.md), [REQ-0006](./req0006_clear-architectural-boundaries.md), [REQ-0009](./req0009_config-driven-remote-access.md), [REQ-000D](./req000D_document-structure-extraction.md)

## Progress Updates

### 2026-10-30

Requirement created (Proposed). Paired with CIP-0019.
