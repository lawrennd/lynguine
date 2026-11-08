---
id: "0009"
title: "Config-driven remote data access before local read"
status: "In Progress"
priority: "High"
created: "2026-08-18"
last_updated: "2026-11-06"
related_tenets:
- explicit-infrastructure
- flow-based-processing
stakeholders:
- Application developers (referia, lamd, other lynguine clients)
- Reviewers and operators who load candidate lists from remote systems
tags:
- requirement
- access
- download
- configuration
- remote
---

# REQ-0009: Config-driven remote data access before local read

> **Remember**: Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

Users can declare, in an interface configuration, that a data item lives on a remote source (URL, Git repository, or similar) and that lynguine must make that data available locally as an explicit access-stage step before the existing read path runs. Authorization, licence acknowledgement, and credential use are explicit. The system does not infer a download from a filename that happens to look like a URL.

Google Sheets already participates as a remote *reader* (`type: gsheet`). CIP-0019 live plugins (Trello, IMAP, Docs catalogue) are also readers. This requirement covers the missing case: **materialise** a remote *file* (or clone a repository), then read it with the ordinary local format handlers (YAML, CSV, Excel, and so on). External syncers that already fill a local tree (for example offlineimap → Maildir) satisfy the same outcome when lynguine only needs to read; the requirement is that fetch-into-cache can also be owned *inside* the flow when the operator asks for it.

**Why this matters**: The explicit-infrastructure and flow-based-processing tenets require access to be a visible stage in the data flow, not a side effect of object construction or an unconnected helper script. Operators should see fetch, authorise, and read as ordered steps.

**Who benefits**: Application authors who currently copy files by hand or call `FileDownloader` outside the flow; reviewers whose allocation lists live on the web or in Git.

## Acceptance Criteria

- [x] An interface `input`, `output`, or `cache` item can name a remote materialise step in configuration (distinct from directory discovery lists).
- [x] When that step is named, lynguine fetches (or confirms a local cache of) the data during flow execution, then reads it with the item's existing `type`.
- [x] When no remote materialise step is named, behaviour is unchanged (local files and live readers only).
- [x] Authorization or credential use for a remote source is explicit and uses the existing credential system where secrets are required.
- [x] Failed fetches fail the flow with an error that names the source and the reason.
- [x] The flow does not download merely because a path or filename resembles a URL.
- [x] Google Sheets and CIP-0019 live plugin types continue to work as readers without requiring a materialise block.
- [x] Directory discovery configuration (CIP-000F) remains usable alongside remote materialise without a naming collision.

## Notes

Transferred from [referia#9](https://github.com/lawrennd/referia/issues/9); tracked as [lynguine#20](https://github.com/lawrennd/lynguine/issues/20). SQL, Trello, IMAP, and Docs *live* access are out of scope for this requirement’s first delivery — they are reader types (CIP-0019 / `gsheet`). File-producing exports (Docs/Drive dump to disk) may later satisfy this requirement when the outcome is still “local file, then read”.

HOW: [CIP-0009](../cip/cip0009.md) (Accepted; next after CIP-0019 plugins). Config key for materialise is `remote:` so it does not collide with CIP-000F directory `source:` lists.

## References

- **Related Tenets**: explicit-infrastructure, flow-based-processing
- **External Links**: https://github.com/lawrennd/lynguine/issues/20
- **CIP**: [CIP-0009](../cip/cip0009.md)

## Progress Updates

### 2026-08-18

Requirement extracted from transferred GitHub issue #20 (originally referia#9). Status Proposed; CIP-0009 describes HOW.

### 2026-10-11

Still Proposed; no acceptance criteria checked. Prerequisites advanced (CIP-000A path confinement merged; CIP-000B credential log fingerprinting merged). CIP-000F closed and introduced a local directory `source` key that collides with CIP-0009's proposed remote `source` block — naming must be resolved before accept. Status comment posted on lynguine#20.

### 2026-10-18

Progress note recovered onto `main`; requirement unchanged (Proposed). Directory `include_start_directory` (CIP-000F follow-on, PR #40) does not resolve the remote `source` naming clash.

### 2026-11-06

CIP-0009 Accepted then implemented on worktree: `remote:` materialise wired through `from_flow`. Acceptance criteria checked; validate before marking Validated.
