---
id: "0011"
title: "Flows can identify redaction terms and apply them to text or PDF separately"
status: "Proposed"
priority: "Medium"
created: "2026-11-08"
last_updated: "2026-11-08"
related_tenets:
  - "explicit-infrastructure"
  - "flow-based-processing"
stakeholders:
  - "referia review flows needing blind or anonymised PDFs"
  - "research-mail / dods-research-mail unit extract scrubbing"
  - "any flow that must scrub identity cues before LLM or shared review"
tags:
  - documents
  - pdf
  - redaction
  - pii
  - text
---

# REQ-0011: Flows can identify redaction terms and apply them to text or PDF separately

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

Lynguine flows can obtain an **explicit list of terms to redact** from one or more identification steps (contact cues in text, structured document fields such as author names, or caller-supplied terms), then **apply** that list to a target medium — plain text and PDF — without the apply step knowing which producer created the list.

Identification and application are separable outcomes. A caller must be able to redact a PDF given only a path and a term list. A caller must also be able to scrub paragraph text for LLM or listing use given the same kind of term list. Producers may run earlier in the flow, be edited by a human, or be omitted when terms are already known.

**Why this matters**: Explicit infrastructure means redaction is not a hidden side effect of one document family. Flow-based processing keeps “discover what to hide” and “hide it in this file” as distinct stages that can be traced and reused.

**Who benefits**: Referia paper/thesis blind copies; mail unit pipelines that scrub `extract_text` while keeping raw `text`; any future attachment or report scrub that reuses the same term contract.

## Acceptance Criteria

- [ ] A flow can produce or accept an explicit term list (strings, with optional kind / match policy) independent of any single document type.
- [ ] The same term list can be applied to plain text so configured identity cues are replaced or removed for downstream compute/display.
- [ ] The same term list can be applied to a PDF to produce a redacted file (identity strings obscured on configured pages).
- [ ] Applying redaction to a PDF does not require running paper front-matter extract or mail PII collect in the same step — terms may come from prior stages or the caller.
- [ ] Failures are visible: empty term list with a non-empty “expected terms” signal, or zero match when terms were non-empty, must not look like silent success.
- [ ] Conservative matching avoids destroying ordinary words (whole-word / stopword-safe behaviour for person-name style terms).

## Notes (Optional)

Document **structure** extract (title/authors as data) remains REQ-000D / CIP-0013. This requirement is about the redaction **term contract** and apply surfaces, not about inventing a new PDF parser.

Mail contact scrubbing that already exists in working trees should converge on this contract rather than remaining a one-off string mutator forever coupled to `split_paragraph_units`.

## References

- **Related Tenets**: explicit-infrastructure, flow-based-processing
- **Related (upstream extract)**: [REQ-000D](./req000D_document-structure-extraction.md)
- **Downstream consumer (referia)**: referia [REQ-001A](https://github.com/lawrennd/referia/blob/main/requirements/req001A_pdf-term-redaction.md) (review redacted PDF from an explicit term list; compose this capability)

## Progress Updates

### 2026-11-08
Requirement created to separate term identification from PDF/text apply; links mail PII scrub work to paper redaction planning (referia CIP-0025).
