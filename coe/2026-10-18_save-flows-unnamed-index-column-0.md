---
id: "2026-10-18_save-flows-unnamed-index-column-0"
title: "save_flows writes index as CSV column 0 when index.name is None"
class: 1
owner: "Neil D. Lawrence"
status: "Closed"
created: "2026-10-18"
last_updated: "2026-10-18"
incident_date: "2026-10-18"
spawned_cips: []
spawned_backlog:
  - "2026-10-18_save-flows-unnamed-index-writes-column-0"
spawned_requirements: []
tags:
  - coe
  - save_flows
  - index
  - csv
  - panel
---

# CoE: save_flows writes index as CSV column 0 when index.name is None

> **Correction of Error** (CIP-0016). CoEs are orthogonal to the WHY→WHAT→HOW→DO
> hierarchy. They examine where the hierarchy broke and produce items at the appropriate
> level to fix it. The CoE itself does not implement fixes — it produces outputs (CIPs,
> backlog tasks, requirements, tripwires) that are implemented separately.
>
> Blameless: focus on process, tooling, and design — not people.
>
> Analysis depth: Class 0 may abbreviate Timeline, Incident questions, and 5 Whys.
> Class 1+ should complete them in full.

## Summary

On 2026-10-18, Panel PhD preliminaries
(`applications/panel/2026-27/phd/info/preliminary.csv`) failed to load under
`referia serve` because the first column was named `0` while the config required
`output.index: Name`. Root cause: `CustomDataFrame.save_flows` / `to_flow`
concat a Series of index values with `name=df.index.name` before
`write_csv(..., index=False)`. When `index.name` is `None`, pandas labels that
column the integer `0`. Creating a missing output frame with
`pd.DataFrame(index=cdf.index, ...)` can leave the name unset even when YAML
specifies `index: Name`. Mitigation: resolve the write column name from
`details['index']` when unset, name new output frames from the flow config, and
add a regression test. Data workaround (rename `0`→`Name` in the CSV) alone was
insufficient — Save would recreate the bad header.

## Severity

**Class**: 1

- Class 0 — Internal only, easily reversible. No user-facing impact.
- Class 1 — Maintainer/contributor workflow impact (not yet externally impactful).
- Class 2+ — External impact: downstream users, deployed behaviour, customer/legal exposure.

**Blast radius**: Any lynguine/referia review whose `output` (or other write)
flow is saved while the in-memory output index has `name is None`. Reload then
fails if config `index` is a string such as `Name`. Observed on Panel PhD
`preliminary.csv`; MPhil had the same symptom earlier and was renamed by hand.

## Impact

Operator could not open the PhD preliminary web review (503 / missing column
`"0"`). Assessment data was still on disk under the wrong header; renaming
restored load, but every subsequent Save risked rewriting `0` until the writer
was fixed. Time spent diagnosing config vs data vs infrastructure.

## Timeline

- Prior — MPhil `preliminary.csv` first column renamed `0`→`Name` after a
  similar load failure (data-only fix)
- 2026-10-18 — PhD Panel config returns load error: column `"0"` not `Name`
- 2026-10-18 — CSV header renamed; load returns 200
- 2026-10-18 — Operator asks whether the bug is fixed; reproduce shows
  `pd.concat([Series(..., name=None), df])` → column `0`
- 2026-10-18 — Fix in `lynguine/assess/data.py` + regression tests; end-to-end
  Save with cleared `index.name` writes `Name,...`

## Evidence / metrics

- PhD CSV header before rename: `0,SessionDate,...`
- Config: `output.index: Name`, `filename: preliminary.csv`
- Minimal reproduce: `Series(list(idx), name=None)` + `concat` → columns
  `[0, ...]`
- After fix: forced `out.index.name = None` then `save_flows()` → header
  starts with `Name,`

## What happened

Output save materialised the index as a data column without guaranteeing a
stable name from the interface. An unnamed index produced CSV column `0`.
Reload used `index: Name` and failed. Creating empty/missing output frames did
not copy `index` from YAML onto `DataFrame.index.name`, so the condition could
recur after a successful data rename.

## Incident questions

### Detection

1. **When did you learn there was impact?**
   - 2026-10-18, when PhD preliminary web load failed after Panel email/UI work.
2. **How did you learn there was impact?**
   - referia serve / WebReviewer error reporting missing column `"0"`; confirmed
     by reading the CSV header.
3. **How can we reduce the time-to-detect in half?**
   - Round-trip test: load config → clear `output.index.name` → save → reload
     must succeed; or assert written CSV first column equals `details['index']`.

### Diagnosis

4. **What was the underlying cause of the impact?**
   - `save_flows`/`to_flow` trusted `df.index.name` alone; pandas defaulted
     unnamed Series columns to `0`.
5. **Was an internal activity underway during the incident?**
   - Yes — Panel MPhil/PhD preliminary web review configuration and Save cycles.
6. **How can we reduce the time-to-diagnose in half?**
   - When load fails on a numeric/unexpected index column name, grep
     `save_flows` / `name=df.index.name` before chasing YAML typos.

### Mitigation

7. **When did impact return to pre-incident levels (or when will it)?**
   - When CSV was renamed *and* the writer fixed so Save cannot recreate `0`.
8. **How does the owner know the system/process is properly restored?**
   - PhD load 200; Save with `index.name is None` still writes `Name`;
     `test_set_value_d_sync.py::TestSaveFlowsIndexColumnName` green.
9. **How did you determine where and how to mitigate?**
   - Traced `save_flows` → `write_csv(index=False)`; reproduced unnamed Series
     → column `0`; fell back to `details['index']`.
10. **How can we reduce the time-to-mitigate in half?**
    - Keep the regression test in the same change as any future index-write
      refactor so the failure mode stays covered.

## 5 Whys

1. **Why** did PhD preliminaries fail to load?
   - Because the CSV first column was `0`, not `Name`.
2. **Why** was the column named `0`?
   - Because save wrote an index Series whose `name` was `None`, and pandas
     labels that `0`.
3. **Why** was `index.name` None?
   - Because creating/holding the output frame did not always set the name from
     YAML `output.index`, and nothing in the write path required it.
4. **Why** didn't the write path use the interface index?
   - Because it only passed `df.index.name` into the Series constructor.
5. **Why** was a prior MPhil rename treated as enough?
   - Because the failure looked like bad data; there was no tripwire that Save
     with an unnamed index must still emit `Name`.

**Root cause(s)**: Output write path did not bind the configured index field
name when `DataFrame.index.name` was unset, so pandas invented column `0`.

## Traceability artifacts missing or incorrect

- [ ] Missing tenet (WHY)
- [ ] Missing requirement (WHAT)
- [ ] Missing CIP (HOW) — local writer fix; no architecture change
- [x] Missing backlog task (DO) — until this CoE / bug task
- [ ] Incorrect/forbidden link direction
- [ ] Template/runtime drift
- [x] Other: no regression asserting CSV index column name on save

## Follow-up outputs

### Backlog tasks

- [x] Fix `save_flows`/`to_flow` index column naming + from_flow create —
      owner: Neil D. Lawrence —
      `backlog/bugs/2026-10-18_save-flows-unnamed-index-writes-column-0.md`

### CIPs

- None (writer defect; no architectural CIP)

### Requirements

- None

### Validation tripwires

- Regression: `TestSaveFlowsIndexColumnName` in
  `lynguine/tests/test_set_value_d_sync.py` (unnamed index + `index: Name`)

## Checklist

- [x] Severity class assigned
- [x] Single-threaded owner named
- [x] Summary written (stand-alone)
- [x] Impact documented
- [x] Timeline documented
- [x] Incident questions answered (Detect / Diagnose / Mitigate)
- [x] 5 Whys completed
- [x] Missing/incorrect traceability artifacts identified
- [x] Follow-up outputs listed with owners (and created)
- [x] CoE status updated to Analysed once outputs are created
- [x] CoE status updated to Closed once outputs are implemented
