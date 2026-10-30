---
id: "2026-10-30_document-form-fields-leverhulme-vp-v1"
title: "form_fields labelled-section path + labeled_kv_form.v1"
status: "In Progress"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
category: "features"
related_cips: ["0013"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-18_document-form-fields-cam-panel-v1"
tags:
- backlog
- features
- access
- compute
- documents
- cip0013
- form-fields
- form-type
---

# Task: form_fields labelled-section path + labeled_kv_form.v1

> Extends CIP-0013 `form_fields` for labelled two-column grant PDFs. Cambridge Panel header parsing is unchanged. Strategy ids name **form types**, not funders.

## Description

Some UK grant-portal primary forms are labelled two-column PDFs (`Title`
then `Professor` on consecutive lines; `ID/Ref: …` on one line). They are
not Cambridge Panel `Family, Title Given` headers.

Add an explicit labelled-form path in the `form_fields` engine when YAML
`params` contain `layout: labeled_kv`, `colon_header`, and/or `sections`.
Ship form type `labeled_kv_form.v1.yml` (field maps are the first
catalogued instance of this layout). Tests use a **synthetic** PDF only
(Ada Host / Visitor One). Do not commit real applicant PDFs.

Referia reviews set `strategy: labeled_kv_form.v1` (do not rely on `auto`
once two `form_fields` strategies exist). Flow kwargs overlay packaged
YAML params so later field maps can live in the application config.

## Acceptance Criteria

- [x] `extract_fields` skips Cambridge `parse_header`/`parse_contact` when `layout` is `labeled_kv` or `colon_header`/`sections` is set
- [x] Consecutive-line pairing; empty labels (Honours/Gender) stored as `None`
- [x] Abstract / programme body is not extracted
- [x] Packaged YAML `labeled_kv_form.v1` auto-registers
- [x] Synthetic fixture + tests; auto recogniser distinguishes Panel vs labelled-kv
- [x] Strategy id and referia extract args contain no funder name
- [ ] Referia preliminary review extracts host/visitor identity only

## Implementation Notes

- `_label_value` is unchanged (whitespace after the label; colons live in YAML prefixes such as `ID/Ref:`).
- `_section_after` returning `None` is treated as empty text.
- FormFieldsEngine summary falls back to `application_id` when `application_number` is absent.
- `YamlStrategy.segment` merges non-None flow kwargs onto packaged `params`.

## Related

- CIP: 0013
- Backlog: 2026-10-18_document-form-fields-cam-panel-v1
- Application: `applications/2026-10-20_leverhulme_visiting-professorship/` (OneDrive referia)

## Progress Updates

### 2026-10-30

Engine path, YAML form type, synthetic builder, and tests added. Referia
review uses `labeled_kv_form.v1`. Identity extract on the real PDF still
to confirm.
