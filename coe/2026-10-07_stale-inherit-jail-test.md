---
id: "2026-10-07_stale-inherit-jail-test"
title: "CIP-000E inherit root extension left a CIP-000A security test expecting PathEscape"
class: 0
owner: "Neil D. Lawrence"
status: "Closed"
created: "2026-10-07"
last_updated: "2026-10-07"
incident_date: "2026-10-07"
spawned_cips: []
spawned_backlog:
  - "2026-10-07_update-inherit-jail-security-test"
spawned_requirements: []
tags:
  - coe
  - path-jail
  - inherit
  - tests
  - cip000E
---

# CoE: CIP-000E inherit root extension left a CIP-000A security test expecting PathEscape

> **Correction of Error** (CIP-0016). CoEs are orthogonal to the WHY→WHAT→HOW→DO
> hierarchy. They examine where the hierarchy broke and produce items at the appropriate
> level to fix it. The CoE itself does not implement fixes — it produces outputs (CIPs,
> backlog tasks, requirements, tripwires) that are implemented separately.
>
> Blameless: focus on process, tooling, and design — not people.
>
> Analysis depth: Class 0 may abbreviate Timeline, Incident questions, and 5 Whys.

## Summary

On 2026-10-07, GitHub Actions run 37579504929 failed on `main` after commit `4f68587`
(CIP-000E): one pytest, `test_from_file_inherit_cannot_leave_jail`, expected
`PathEscapeError` when a child inherited `../outside`, but CIP-000E intentionally
extends `allowed_roots` with `inherit.directory`. Impact was internal CI only
(698 passed, 1 failed). Mitigation is updating the stale CIP-000A-era test to match
the new inherit policy while keeping non-inherit and `cwd_sandbox` escape coverage.

## Severity

**Class**: 0

- Class 0 — Internal only, easily reversible. No user-facing impact.
- Class 1 — Maintainer/contributor workflow impact (not yet externally impactful).
- Class 2+ — External impact: downstream users, deployed behaviour, customer/legal exposure.

**Blast radius**: Python Tests workflow on `main` (`build (3.11)`); no deployed
behaviour change beyond the intentional CIP-000E inherit policy already committed.

## Impact

CI red on `main` for one security regression test that encoded the pre-CIP-000E
expectation. Local contributors running the full suite see the same failure. No
external user or HTTP path-jail regression (cwd-sandbox inherit still refuses escape).

## Timeline

- 2026-10-07 — CIP-000E lands on `main` (`4f68587`): inherit extends `allowed_roots`; new `test_from_file_inherit_allows_sibling_directory` added
- 2026-10-07 — CI run 37579504929 fails: `test_from_file_inherit_cannot_leave_jail` DID NOT RAISE
- 2026-10-07 — Diagnosis via CI investigation + local reproduce; CoE + backlog + test update

## Evidence / metrics

- Actions annotation: process exit code 1 on “Run tests with pytest and coverage”
- Failure: `lynguine/tests/test_config_interface.py::test_from_file_inherit_cannot_leave_jail` — `Failed: DID NOT RAISE PathEscapeError`
- Suite: ~698 passed, 1 failed (Python 3.11)
- Contrasting passing test: `test_from_file_inherit_allows_sibling_directory` in `test_access_paths.py`

## What happened

A CIP-000A security test still asserted that `inherit.directory: ../outside` must
PathEscape. CIP-000E changed that policy for trusted local `from_file` inherit, but
the old assertion was not updated in the same change set.

## Incident questions

### Detection

1. **When did you learn there was impact?**
   - 2026-10-07, when reviewing the failed Actions run linked from chat.
2. **How did you learn there was impact?**
   - GitHub Actions failure on push to `main`; confirmed by reading the stale test vs CIP-000E diff.
3. **How can we reduce the time-to-detect in half?**
   - When a CIP changes security policy encoded in tests, treat “update or retire conflicting assertions” as an explicit CIP implementation checklist item before merge.

### Diagnosis

4. **What was the underlying cause of the impact?**
   - Policy change (inherit may extend roots) shipped with a new positive test, without retiring the older negative test that encoded the previous policy.
5. **Was an internal activity underway during the incident?**
   - Yes — CIP-000E / inherit-extends-allowed-roots landing on `main`.
6. **How can we reduce the time-to-diagnose in half?**
   - Grep for related assertions (`PathEscapeError` + `inherit`) when changing path-jail behaviour; keep negative and positive security tests in the same module or cross-link them in the CIP.

### Mitigation

7. **When did impact return to pre-incident levels (or when will it)?**
   - When the stale test is updated and CI is green on the fix commit.
8. **How does the owner know the system/process is properly restored?**
   - Updated test passes locally; full pytest job green; cwd-sandbox inherit escape tests still fail as intended.
9. **How did you determine where and how to mitigate?**
   - Compared `4f68587` interface change + new sibling-inherit test with the failing CIP-000A-era assertion; policy docs already state only explicit `inherit.directory` may extend the jail.
10. **How can we reduce the time-to-mitigate in half?**
    - Land policy-changing security diffs only with a paired “conflicting tests” checklist item so the fix is in the same PR as the behaviour change.

## 5 Whys

1. **Why** did CI fail?
   - Because one test expected `PathEscapeError` and the new code did not raise it.
2. **Why** did the test expect PathEscape?
   - Because under CIP-000A’s initial jail, inherit used the child’s roots only, so `../outside` escaped.
3. **Why** does the code no longer raise?
   - Because CIP-000E intentionally appends `inherit.directory` to `allowed_roots` for sibling/ancestor parent configs.
4. **Why** wasn’t the old test updated with that change?
   - Because the change set added a new positive regression and backlog notes, but did not inventory existing negative assertions that encoded the old policy.
5. **Why** was that inventory easy to miss?
   - Because there was no CIP/implementation checklist item requiring a search for conflicting security tests when path-jail policy widens.

**Root cause(s)**: Behaviour-changing security policy landed without a forced pass over
existing negative tests that encoded the prior policy.

## Traceability artifacts missing or incorrect

- [ ] Missing tenet (WHY)
- [ ] Missing requirement (WHAT)
- [ ] Missing CIP (HOW) — CIP-000E existed; gap was follow-through on conflicting tests
- [x] Missing backlog task (DO) — no task specifically to retire/update the CIP-000A-era inherit PathEscape assertion
- [ ] Incorrect/forbidden link direction
- [ ] Template/runtime drift
- [x] Other: policy-changing commit incomplete relative to existing security test inventory

## Follow-up outputs

### Backlog tasks

- [x] Update `test_from_file_inherit_cannot_leave_jail` to match CIP-000E inherit root extension — owner: Neil D. Lawrence — `backlog/bugs/2026-10-07_update-inherit-jail-security-test.md`

### CIPs

- None (CIP-000E already covers the policy; this is test alignment)

### Requirements

- None

### Validation tripwires

- Optional later: CIP checklist note “search for conflicting PathEscape/inherit tests when widening the jail” (defer unless recurrence)

## Checklist

- [x] Severity class assigned
- [x] Single-threaded owner named
- [x] Summary written (stand-alone)
- [x] Impact documented
- [x] Timeline documented (abbreviated Class 0)
- [x] Incident questions answered (Detect / Diagnose / Mitigate)
- [x] 5 Whys completed (abbreviated OK for Class 0)
- [x] Missing/incorrect traceability artifacts identified
- [x] Follow-up outputs listed with owners (and created)
- [x] CoE status updated to Analysed once outputs are created
- [x] CoE status updated to Closed once outputs are implemented
