---
id: "2026-11-08_document-paper-frontmatter-v1"
title: "paper_frontmatter aspect + academic_paper_front.v1 (title/authors)"
status: "Completed"
priority: "High"
created: "2026-11-08"
last_updated: "2026-11-08"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-model-pdf-reader"
- "2026-10-18_document-form-fields-cam-panel-v1"
tags:
- backlog
- features
- access
- compute
- documents
- cip0013
- paper-frontmatter
- referia-cip0025
---

# Task: paper_frontmatter aspect + academic_paper_front.v1

> Extends CIP-0013 for a **new aspect** (academic first-page title/authors).  
> Consumed by referia [CIP-0025](https://github.com/lawrennd/referia/blob/main/cip/cip0025.md) Phase 1 (author-name redaction).

## Plan (summary)

1. Add aspect **`paper_frontmatter`** — one structured record per PDF (title + authors).
2. Add shared **`paper_frontmatter` engine** that interprets YAML params (stop headings, max pages).
3. Ship strategy **`academic_paper_front.v1` as YAML** under `strategies/academic_paper_front.v1.yml`.
4. Expose via compute (`document_segment` with `aspect: paper_frontmatter`, plus `extract_paper_frontmatter` helper).
5. Synthetic fixtures + tests (no real author PII in-repo).

## Motivation

Referia CIP-0025 needs title/author extraction before redaction — same capability shape as Panel `extract_form_fields`, different document family. End-of-paper `references` already exists; this is front-of-paper identity.

## Description

### Aspect: `paper_frontmatter`

- **Grain (v1):** one row per document.
- **Output fields (initial):** `title`, `authors` (list of strings), `authors_raw`, optional `emails` from the front-matter region.
- Distinct from `body_chunks` / `form_fields` / `references`.

### Strategy: `academic_paper_front.v1`

Typical digital single-column / PMLR-like first page:

1. Restrict to first `max_pages` (default 1).
2. Stop region at Abstract / Introduction / Keywords (YAML `stop_headings`).
3. First substantial line → title; following author-like lines until affiliation/email/stop → authors.
4. Split authors on commas, `and`, `&`.

### Out of scope (this task)

- OCR / scanned papers
- Full ACM/IEEE two-column edge cases
- Font-size on Block (optional follow-on)
- Referia soft-fill / redaction (CIP-0025 Phases later)

## Acceptance Criteria

- [x] Aspect `paper_frontmatter` supported by strategy registry + engine
- [x] Strategy `academic_paper_front.v1` registered from YAML
- [x] Fields at least: `title`, `authors` (list), `authors_raw`
- [x] `extract_paper_frontmatter` compute helper returns one dict (like `extract_form_fields`)
- [x] Synthetic fixture + unit tests; recogniser `auto` picks strategy on Abstract-bearing papers
- [x] Existing `form_fields` / `references` tests remain green

## Related

- CIP: 0013 (lynguine)
- referia CIP-0025 / REQ-001A

## Progress Updates

### 2026-11-08
Task created (In Progress) with CIP-0025 Accepted; implementation starting in `cip0013-paper-frontmatter` worktree.

Engine + YAML strategy + `extract_paper_frontmatter` + fixtures/tests landed. 11 new tests green; form_fields and references regression suites green. Status → Completed.
