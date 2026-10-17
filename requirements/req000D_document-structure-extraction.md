---
id: "000D"
title: "Document structure and aspect extraction from PDF and DOCX"
status: "In Progress"
priority: "High"
created: "2026-10-17"
last_updated: "2026-10-17"
related_tenets:
  - "explicit-infrastructure"
  - "flow-based-processing"
stakeholders:
  - "pub-dialogue (PDF report corpora)"
  - "ai-dialogue-formats (DOCX transcripts)"
  - "mlresearch / PMLR (academic PDF reference lists)"
  - "referia (document review flows)"
tags:
  - "access"
  - "documents"
  - "pdf"
  - "docx"
  - "extraction"
---

# REQ-000D: Document structure and aspect extraction from PDF and DOCX

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

Users can load PDF and DOCX files through lynguine flows and obtain structured units suitable for downstream compute — paragraphs, sections, dialogue-style units, or bibliographic references — without each application inventing its own one-off parser.

Different documents of the same mime type need different segmentation and reference-parsing behaviour. The system must make that variation explicit (selectable or auto-recognised strategies) rather than hiding a single heuristic that works on one corpus and fails on another.

**Why this matters**: Aligns with explicit infrastructure (no magic parsers) and flow-based processing (access produces structured rows; assess/address compute runs on those rows).

**Who benefits**: pub-dialogue (report PDFs → chunks), ai-dialogue-formats (DOCX → units), mlresearch volume PDFs (in-paper reference lists), and any referia-style review flow that needs document text or citations as data.

## Acceptance Criteria

- [ ] A lynguine flow can declare a PDF or DOCX source and produce a tabular result with explicit unit identity (path, unit id, order) and text.
- [ ] At least three aspects are supported as first-class outcomes: body segments (paragraphs/chunks), dialogue-oriented units, and bibliographic references.
- [ ] Layout / reference formatting variation is handled by named strategies (manual select and/or recogniser), not a single undocumented heuristic.
- [ ] A fixture-based testing programme covers diverse real-world PDFs (public-dialogue reports, academic proceedings papers, and at least one DOCX transcript shape) with expected segmentation / reference outcomes.
- [ ] Domain LLM steps (phrase extract, cluster, …) remain optional compute on top of structured units — not required for access to succeed.

## Notes (Optional)

Sibling packages already implement corpus-specific access (`pub_dialogue.access.extract_chunks_from_pdf`, `dialogue_formats.access.load_corpus`). This requirement is about making the shared pattern available as lynguine infrastructure, not absorbing those research pipelines wholesale.

In-PDF reference extraction (end-of-paper lists) is distinct from volume-level BibTeX already maintained for PMLR publishing.

## References

- **Related Tenets**: explicit-infrastructure, flow-based-processing
- **Related CIP**: [CIP-0013](../cip/cip0013.md)
- **Related**: [CIP-0004](../cip/cip0004.md) (LLM compute), [CIP-0007](../cip/cip0007.md) (vongole / files compute placement)

## Progress Updates

### 2026-10-17
Requirement created from discussion of wiring pub-dialogue PDFs and ai-dialogue-formats DOCX through lynguine, plus mlresearch reference extraction and pluggable layout/reference recognisers.

CIP-0013 Accepted. Placement: lynguine access (not vongole). Scanned PDFs: detect in v1, OCR future. Status → Ready.

CIP-0013 moved to In Progress; backlog slices created under `backlog/features/2026-10-17_document-*`. Status → In Progress.
