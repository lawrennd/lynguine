---
id: "2026-10-18_document-form-fields-cam-panel-v1"
title: "form_fields aspect + cam_panel_application.v1 (Cambridge Panel PG PDFs)"
status: "In Progress"
priority: "High"
created: "2026-10-18"
last_updated: "2026-10-18"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-17_document-model-pdf-reader"
- "2026-10-17_document-segment-pub-dialogue-v1"
tags:
- backlog
- features
- access
- compute
- documents
- cip0013
- panel
- form-fields
---

# Task: form_fields aspect + cam_panel_application.v1

> Implements CIP-0013 for a **new aspect** (structured form/key–value fields), not paragraph chunking.

## Plan (summary)

1. Add aspect **`form_fields`** — one structured record per PDF (wide / nested), not exploded body chunks.
2. Add shared **`form_fields` engine** (Python) that interprets YAML params (labels, section bounds, date aliases).
3. Ship strategy **`cam_panel_application.v1` as YAML** (not a ported Python script class) under `strategies/cam_panel_application.v1.yml`.
4. Expose via compute (`document_segment` with `aspect: form_fields`, plus optional `extract_form_fields` helper).
5. Synthetic fixtures + tests; then wire referia Panel flows to seed `candidates.csv`.

Prototype (behavioural reference for parity only; do not commit real PDFs/PII):

`~/OneDrive/referia/applications/panel/2026-27/experiments/extract_panel_applicant.py`

Validated on early Gates 2026–27 MPhil + PhD department-copy PDFs (local only; do not name applicants or USNs here).

## Motivation

Cambridge Panel PG application PDFs (`panel.admin.cam.ac.uk`) need **applicant header + contact** extraction:

| Need | Why `pub_dialogue.v1` fails |
|------|------------------------------|
| Name, USN, application number, course, dates | Form/label soup on page 0, not prose paragraphs |
| Candidate email + address | Under `Personal Information` → `Contact`, **not** page 0 |
| Avoid referee emails | Whole-PDF email harvest confuses referees with candidate |

This is the same CIP-0013 pattern as `references`: locate regions, parse records — different aspect and grain.

## Description

### Aspect: `form_fields`

- **Grain (v1):** **one row per document** (dict / wide fields). Do **not** explode to one row per field unless a later mode requests it.
- **Output fields (initial):** see Acceptance Criteria.
- Distinct from `body_chunks` / `dialogue_units` / `references`.

### Strategy: `cam_panel_application.v1` (YAML + `form_fields` engine)

Corpus-shaped YAML strategy for CST Panel “Department Copy” postgraduate application PDFs. Registration path: packaged YAML → `YamlStrategy` → `form_fields` engine (CIP-0013).

**Page 0 (header):**

- Name line: `FamilyName, Title GivenNames` (normalise shouted caps, e.g. `SMITH` / `Jane ANN`)
- `Application Number`, `USN`
- Award + course title (`MPhil` / `PhD`); strip smashed `Course` token; prefer separate term field over embedding term in title
- `date_submitted` → ISO `YYYY-MM-DD` (handle Panel `Sept`)
- `course_start_date` → ISO; parse `(MT|LT|ET YYYY)` into `course_start_term`
- Mode of study, nationality, fee status

**Contact region (full doc, before referees):**

- Section: `Personal Information` → `Contact`
- `Email <addr>` on one line (Panel form style)
- `Contact address` until `Phone` / `Valid until` / `Home address`
- **Do not** take emails from `Referee Details` blocks or later CV/letter text

**Audit fields:** `emails_all`, `emails_referee`, `email_ambiguous` (Contact region has >1 email)

### Compute / YAML surface

```yaml
compute:
  - function: document_segment   # or extract_form_fields helper
    field: applicant            # single dict, or flattened columns — decide in impl
    row_args:
      path: applicationPdf
    args:
      reader: pdf
      strategy: cam_panel_application.v1
      aspect: form_fields
      root: ../files
```

Optional convenience (mirrors `extract_references`):

```yaml
- function: extract_form_fields
  field: applicant
  row_args:
    path: applicationPdf
  args:
    strategy: cam_panel_application.v1
    root: ../files
```

### Recogniser

- Boost `cam_panel_application.v1` when page-0 text matches `Application Number:` + `USN:` + (`MPhil in`|`PhD in`) and/or `Postgraduate Application Form`.
- `strategy: auto` + `aspect: form_fields` should resolve to this strategy when only one form strategy exists.

### Privacy / fixtures

- Do **not** commit real applicant PDFs to lynguine.
- Build **synthetic** Panel-like PDF fixtures (header + Personal Information/Contact + Referee Details with decoy emails) under `lynguine/tests/fixtures/documents/`.
- Keep real-PDF validation in referia `panel/…/experiments/` (local only).

### Out of scope (this task)

- OCR / scanned packs
- Body statement chunking (use `pub_dialogue.v1` or a later Panel body strategy)
- Writing back into Panel Marking UI
- referia `_referia.yml` wiring (follow-on backlog in referia once lynguine lands)

## Acceptance Criteria

- [x] Aspect `form_fields` documented in CIP-0013 aspect table and supported by the strategy registry
- [x] Strategy `cam_panel_application.v1` registered from YAML; `segment(document)` (or dedicated extract path) returns structured applicant fields via `form_fields` engine
- [x] Fields at least: `family`, `given`, `title`, `application_number`, `usn`, `award`, `course_title`, `course_start_date` (ISO), `course_start_term`, `date_submitted` (ISO), `email`, `contact_address`
- [x] Candidate email taken from Contact section; referee emails excluded from `email`
- [x] Dates normalised to `YYYY-MM-DD`; Cambridge term parsed to `MT|LT|ET YYYY`
- [x] Synthetic fixtures + unit tests for header, contact, and referee-email non-confusion
- [x] Compute entry usable from YAML (`document_segment` and/or `extract_form_fields`)
- [ ] Prototype behaviour parity notes vs `extract_panel_applicant.py` (link path in Related) — local validation deferred

## Implementation Notes

### Suggested code layout

```
lynguine/access/documents/
  engines/form_fields.py                   # shared engine (algorithms)
  strategies/loader.py                     # YAML → YamlStrategy
  strategies/cam_panel_application.v1.yml  # params + recogniser boosts
  segment.py                               # extract_form_fields helper
  strategy.py                              # discover packaged *.yml
lynguine/assess/compute.py                 # optional extract_form_fields
lynguine/tests/test_document_form_fields_panel.py
lynguine/tests/fixtures/documents/builders/panel_layouts.py
```

### Port checklist (from experiment script → engine + YAML)

1. Move parse helpers into `form_fields` engine: name line, ISO dates (`Sept` alias), start-date + term, contact section bounds, referee-block email audit.
2. Put corpus-specific labels / section paths / month aliases / recogniser substrings in `cam_panel_application.v1.yml` `params` / `recogniser`.
3. Adapt to `Document` model: `pages[0].text` for header; page texts joined with newlines for Contact (line-oriented Panel forms).
4. Emit one `Unit` with `aspect=form_fields`, fields in `extras`, plus `segment_engine`; `extract_form_fields` returns that dict for compute ergonomics.
5. Path confinement: reuse `allowed_roots` / `root` like other CIP-0013 computes.

### referia follow-on (not this task)

After merge, referia Panel configs can:

```yaml
input:
  compute:
    - function: extract_form_fields
      # flatten into given / family / Application Number for candidates.csv seed
```

Local experiment path to retire or thin-wrap once lynguine ships.

## Related

- CIP: 0013
- REQ: 000D (via CIP)
- Prototype: `$REFERIAl/2026-27/experiments/extract_panel_applicant.py` (local only)
- Consumer: referia `applications/panel/2026-27/{mphil,phd}/`

## Progress Updates

### 2026-10-18

Task created (Proposed). Prototype script validated on two early Gates Panel PDFs (local; no applicant identifiers recorded here); email/referee disambiguation and ISO/term date parsing working as first try.

Design update: ship as YAML strategy + shared `form_fields` engine (CIP-0013 YAML registration path), not a Python strategy class.

Implementation landed in lynguine: `engines/form_fields.py`, `strategies/loader.py`, `strategies/cam_panel_application.v1.yml`, `extract_form_fields` compute helper, synthetic Panel fixture + tests. Status → In Progress pending local parity check against the referia prototype (no PII in repo).
