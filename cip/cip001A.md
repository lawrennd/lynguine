---
author: "Neil D. Lawrence"
created: "2026-11-08"
id: "001A"
last_updated: "2026-11-08"
status: "Proposed"
compressed: false
effort: medium
priority: medium
related_requirements: ["0011"]
related_cips: ["0013"]
tags:
  - cip
  - documents
  - pdf
  - redaction
  - pii
  - text
  - explicit-infrastructure
title: "Shared RedactTerms contract with text and PDF apply"
---

# CIP-001A: Shared RedactTerms contract with text and PDF apply

> CIPs describe HOW to achieve requirements (WHAT).  
> Implements [REQ-0011](../requirements/req0011_term-based-document-redaction.md).

## Status

- [x] Proposed - Initial idea documented
- [ ] Accepted - Approved, ready to start work
- [ ] In Progress - Actively being implemented
- [ ] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented
- [ ] Deferred - Postponed

## Summary

Introduce an explicit **RedactTerms** value (list of terms with optional kind and match policy), plus two apply surfaces that consume it:

1. **Text apply** — replace/scrub in strings (mail `extract_text`, any text path).
2. **PDF apply** — produce a redacted PDF from `(source_path, terms, page_scope)` with no knowledge of how terms were discovered.

**Producers** (identification) stay separate modules/helpers and only *emit* RedactTerms:

- contact-PII collect from body / sender (refactor of today’s `redact_contact_pii`)
- paper authors / emails from CIP-0013 `paper_frontmatter` (already a producer of structured fields; mapping to terms is trivial)
- caller-supplied / human-edited lists

Referia CIP-0025 owns review wiring only; it must not reimplement PDF string search.

## Motivation

Mail unit scrubbing and paper-author blind copies both need “hide these identity strings,” but they started as different stories. CIP-0025 currently describes extract-then-redact as one paper pipeline. That couples PDF blackout to academic front matter and leaves mail with a one-off mutator.

We need one infrastructure contract so a flow can redact a PDF given only a term list, and so mail and paper share whole-word / stopword-safe matching.

## Detailed Description

### Layering

```
Producers (identify)                    Shared contract              Consumers (apply)
─────────────────────                   ───────────────              ─────────────────
collect_contact_pii_terms(text, …) ─┐
paper_frontmatter → authors/emails ─┼─► RedactTerms ──┬─► redact_text(text, terms)
manual / column list ───────────────┘                 └─► redact_pdf(src, dest, terms, pages=…)
```

### RedactTerms (v1 shape)

Illustrative; exact type chosen at Accept → backlog:

| Field | Purpose |
|-------|---------|
| `value` | String to match |
| `kind` | Optional: `name`, `email`, `phone`, `url`, `other` (drives placeholder or PDF style later) |
| `match` | `whole_word` (default for names) or `literal` (emails/URLs) |
| `source` | Optional provenance: `contact_pii`, `paper_frontmatter`, `manual` |

Deduplicate by normalised value; longest-first apply order for overlapping name phrases.

### Shared matcher

Whole-word name replacement and stopword / min-token guards live **once** (today’s logic in `lynguine.util.text`). Both `redact_text` and PDF hit-finding call the same matcher so “at” cannot destroy “Mathematics” in either medium.

### Text path (mail convergence)

Refactor current behaviour:

| Today | Target |
|-------|--------|
| `redact_contact_pii(text, names=…)` does collect+apply | `collect_contact_pii_terms(…)` → RedactTerms; `redact_text(text, terms)` applies |
| `split_paragraph_units(..., redact_pii=True)` | Collect once per message; apply per paragraph into `extract_text` |

Keep a thin `redact_contact_pii` wrapper that collect+applies for backward compatibility until callers migrate.

### PDF path

New lynguine helper / document op (name TBD at backlog: `redact_pdf` / prepare-style function):

**Inputs:** source PDF path, destination path (or bytes), RedactTerms, optional page window (default first N pages configurable).

**Behaviour (v1):**

1. Search page text for term occurrences with the shared matcher.
2. Add redaction boxes (or equivalent) and apply; write dest.
3. Return match counts / warnings: zero matches when terms non-empty → explicit warning payload, not silent “success.”

**Non-goals (v1):** OCR of scanned PDFs; layout-aware affiliation region wipe without terms; publisher-specific heuristics (those belong in extract producers).

Library choice (PyMuPDF redactions vs existing stack) is an Accept → backlog decision; prefer one dependency already used or easily optional.

### Relation to CIP-0013

CIP-0013 remains the home for **document structure extract** (`paper_frontmatter`, `form_fields`, …). This CIP does **not** fork extractors. It only consumes structured fields (or text) as term producers and owns apply + the shared term contract.

### Alternatives considered

| Approach | Why not |
|----------|---------|
| Keep PDF redact only in referia CIP-0025 | Duplicates matching rules; mail cannot reuse; violates progressive augmentation of infrastructure |
| One mega “anonymise_paper(pdf)” API | Hides stages; cannot redact with a hand-edited list alone |
| LLM-only term discovery as the contract | Non-reproducible default; fine as a future producer, not the term schema |

## Implementation Plan

1. **Accept design** — confirm RedactTerms fields, PDF library constraint, wrapper deprecation path for `redact_contact_pii`.
2. **Shared matcher + RedactTerms** — extract from existing text util; unit tests (including Mathematics / stopword regressions).
3. **Text apply + contact collect split** — mail `split_paragraph_units` uses collect then apply; commit scrub work currently on working tree.
4. **`redact_pdf`** — fixture PDF with planted strings; assert boxes/removal and zero-match warning.
5. **Docs** — short API note; point referia CIP-0025 at this CIP for Phase 2.
6. **Backlog tasks** — only after Accept (per VibeSafe).

## Backward Compatibility

- Existing `redact_contact_pii` / `split_paragraph_units(..., redact_pii=True)` behaviour preserved via wrappers.
- No change to CIP-0013 aspects or referia `editpdf` until referia wires `redact_pdf`.
- New APIs are additive.

## Testing Strategy

- Unit: collect terms from sender/body; whole-word safety; profile URL kinds.
- Unit: `redact_text` placeholders.
- Fixture PDF: plant author-like strings; redact; assert absence in extractable text; zero-match warning when terms miss.
- Regression: existing paragraph-unit and document-segment tests stay green.

## Related Requirements

- [REQ-0011](../requirements/req0011_term-based-document-redaction.md) — term identify and apply separately (text + PDF).
- Related extract (not implemented here): [REQ-000D](../requirements/req000D_document-structure-extraction.md) / [CIP-0013](./cip0013.md).
- Downstream: referia REQ-001A (redact PDF from terms); CIP-0025 is one HOW (`paper_frontmatter` soft-fill optional → this CIP’s `redact_pdf`).

## Implementation Status

- [x] Draft CIP + REQ-0011 (Proposed)
- [ ] Accept CIP; create backlog slices
- [ ] RedactTerms + shared matcher
- [ ] Contact collect / text apply split (mail)
- [ ] `redact_pdf` + fixtures
- [ ] Validation; mark Implemented / Closed

## References

- Working mail scrub: `lynguine.util.text.redact_contact_pii` / `split_paragraph_units` (uncommitted / in-progress on main)
- referia [CIP-0025](https://github.com/lawrennd/referia/blob/main/cip/cip0025.md) — review composition only after this infrastructure exists
- Tenets: explicit-infrastructure, flow-based-processing
