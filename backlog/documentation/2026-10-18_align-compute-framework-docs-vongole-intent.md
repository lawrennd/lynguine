---
id: "2026-10-18_align-compute-framework-docs-vongole-intent"
title: "Align compute docs and CIP cross-links with vongole intent"
status: "Proposed"
priority: "High"
created: "2026-10-18"
last_updated: "2026-10-18"
category: "documentation"
related_cips: ["0007"]
owner: "lawrennd"
dependencies: []
tags:
- backlog
- documentation
- vongole
- compute
---

# Task: Align compute docs with vongole intent

> Documentation / CIP cleanup that may proceed while CIP-0007 is still **Proposed**.
> This does **not** create the vongole package or move code.

## Description

Cross-repo compute audit (2026-10-18) showed that CIP-0007’s vongole intent is under-documented in live docs, and several CIPs still imply outdated placement (e.g. PDF under vongole `files.py`, assessment functions as if they lived in lynguine, three-phase execution as if fully wired).

Update lynguine documentation and related CIP/requirement pointers so the **intended** stack and **live** stack are both explicit:

```
Target: lynguine → vongole → apps (referia)
Live:   lynguine → referia (vongole missing; assessment fns in referia)
```

## Acceptance Criteria

- [ ] `docs/compute_framework.md` states intended vs live inheritance; lists lynguine’s actual five registered functions; marks assessment catalog as referia-today / vongole-target; does not over-claim honest `precompute`/`postcompute` (point at CIP-0011)
- [ ] CIP-0004 already retargeted to vongole (2026-10-18) — ensure `compute_framework.md` / related docs match (not “LLM in lynguine”)
- [ ] CIP-0011 Related Work links CIP-0007 as consumer of honest phases
- [ ] CIP-0013 Related Work already supersedes vongole `files.py` — confirm wording still matches revised CIP-0007
- [ ] REQ-0006 progress note references 2026-10-18 CIP-0007 revision
- [ ] CIP README (if it lists CIP summaries) mentions vongole intent for CIP-0007

## Implementation Notes

- Prefer short “As of / Target / Live” callouts over rewriting history.
- Do not delete superseded sketches; mark them superseded and link CIP-0013 / CIP-0011.
- referia-side doc cleanup is a separate backlog task in the referia repo.

## Related

- CIP: 0007 (Proposed — revised 2026-10-18)
- CIP: 0004, 0011, 0013
- REQ: 0006
- Companion: referia `backlog/documentation/2026-10-18_align-compute-docs-vongole-intent.md`

## Progress Updates

### 2026-10-18

Task created after CIP-0007 design revision. Status Proposed; work may start without Accepting CIP-0007.
