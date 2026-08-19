---
id: "0009"
title: "Config-driven remote data access before local read"
status: "Proposed"
priority: "Medium"
created: "2026-08-18"
last_updated: "2026-08-18"
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

Google Sheets already participates as a remote *reader* (`type: gsheet`). This requirement covers the missing case: fetch a remote *file* (or clone a repository), then read it with the ordinary local format handlers (YAML, CSV, Excel, and so on).

**Why this matters**: The explicit-infrastructure and flow-based-processing tenets require access to be a visible stage in the data flow, not a side effect of object construction or an unconnected helper script. Operators should see fetch, authorise, and read as ordered steps.

**Who benefits**: Application authors who currently copy files by hand or call `FileDownloader` outside the flow; reviewers whose allocation lists live on the web or in Git.

## Acceptance Criteria

- [ ] An interface `input`, `output`, or `cache` item can name a remote source in configuration.
- [ ] When a remote source is named, lynguine fetches (or confirms a local cache of) the data during flow execution, then reads it with the item's existing `type`.
- [ ] When no remote source is named, behaviour is unchanged (local files only).
- [ ] Authorization or credential use for a remote source is explicit and uses the existing credential system where secrets are required.
- [ ] Failed fetches fail the flow with an error that names the source and the reason.
- [ ] The flow does not download merely because a path or filename resembles a URL.
- [ ] Google Sheets continues to work as a reader type without requiring a fetch-then-read source block.

## Notes

Transferred from [referia#9](https://github.com/lawrennd/referia/issues/9); tracked as [lynguine#20](https://github.com/lawrennd/lynguine/issues/20). SQL and other live-query backends are out of scope for the first delivery of this requirement; they would be additional reader types, not file fetches.

## References

- **Related Tenets**: explicit-infrastructure, flow-based-processing
- **External Links**: https://github.com/lawrennd/lynguine/issues/20

## Progress Updates

### 2026-08-18

Requirement extracted from transferred GitHub issue #20 (originally referia#9). Status Proposed; CIP-0009 describes HOW.
