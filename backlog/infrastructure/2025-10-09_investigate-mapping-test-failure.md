---
id: "2025-10-09_investigate-mapping-test-failure"
title: "Investigate why identity mapping bug cannot be minimally reproduced"
status: "Proposed"
priority: "Medium"
created: "2025-10-09"
last_updated: "2025-10-10"
owner: "lawrennd"
github_issue: null
dependencies: null
tags:
- backlog
- investigation
- testing
- mapping
---

# Task: Investigate Mapping Bug Reproducibility Failure

## Description

A bug was fixed where interface mappings couldn't override auto-generated identity mappings (see `2025-10-09_mapping-conflict-with-identity-mappings.md`). The fix works on the real-world scenario (214 people records), but coding agent struggled with multiple attempts to create a minimal test case.

This inability to reproduce the bug in isolation indicates a **gap in understanding of the code's behaviour** and represents a testing/debugging weakness that should be investigated.

## The Bug (Successfully Fixed)

**Real scenario that fails without fix:**
- Location: `~/OneDrive/referia/people/_referia.yml`
- Configuration: vstack with multiple sources, top-level mapping `jobTitle: job_title`
- Error: `ValueError: Column "job_title" already exists in the name-column map...`
- Fix: Recognize identity mappings as auto-generated in `update_name_column_map()`

**What we expected:**
1. First source has `job_title` column (valid variable name)
2. `_augment_column_names()` creates identity mapping: `job_title -> job_title`
3. Interface mapping tries to apply: `jobTitle -> job_title`
4. Conflict raises ValueError

## Attempted Reproductions (All Failed)

All of these scenarios *passed* even without the fix:

### 1. Basic vstack with add_columns
```yaml
type: vstack
index: Name
mapping:
  jobTitle: job_title
specifications:
- type: markdown_directory
  add_columns: [job_title]
- type: markdown_directory
  add_columns: [job_title]
```
*Result:* Passed without fix (no conflict)

### 2. Column in source data
```yaml
specifications:
- type: markdown_directory
  # job_title IN the source markdown frontmatter
```
*Result:* Passed without fix (no conflict)

### 3. With compute fields using row_args
```yaml
compute:
- field: fullName
  function: render_liquid
  row_args:
    jobTitle: job_title
```
*Result:* Passed without fix (no conflict)

### 4. Multiple sources with different types
- Markdown directories
- YAML files
- Excel files
**Result:** Passed without fix (no conflict)

## Debug Observations

### Mapping Call Sequence (from traced execution)
```
[1] update_name_column_map(jobTitle, job_title)  # Interface mapping applied FIRST
    Before: _column_name_map = {}
    After:  _column_name_map = {'job_title': 'jobTitle'}

[2] _augment_column_names called
    Before: _column_name_map = {'job_title': 'jobTitle'}  # Already has mapping
    # job_title doesn't get identity mapping because it's already mapped!
```

**Key insight:** In minimal tests, the interface mapping is applied *before* augmentation, so there's no identity mapping to conflict with.

**Question:** In the real scenario, why does the identity mapping get created *before* the interface mapping is applied?

## Questions to Investigate

1. **Timing:** When exactly are mappings applied in the real scenario vs. test scenarios?
   - Does `from_flow()` process vstackspecifications differently?
   - Is there a difference between specification-level and interface-level mappings?
   - Are there multiple CustomDataFrame instances being created and merged?

2. **Inheritance:** How do mappings flow through the vstack hierarchy?
   - Line 1012 in `from_flow()`: `mapping = item["mapping"]` (gets spec-level mapping)
   - Line 2961 in `_finalize_df()`: processes `interface["mapping"]` (top-level)
   - Which is applied first? Does the order differ for vstack?

3. **Index Column Handling:** Is the `Name` index column special?
   - The real config computes the Name index with liquid templates
   - Does index handling affect mapping order?

4. **Multiple Data Types:** Does mixing different source types matter?
   - Real scenario: markdown_directory, yaml, excel
   - Do different readers apply mappings differently?

5. **State Persistence:** Are mappings persistent across specifications?
   - Debug shows each spec gets fresh `_column_name_map = {}`
   - But real error suggests mappings persist - how?

## Acceptance Criteria

- [ ] Understand the exact sequence of operations that causes the identity mapping conflict
- [ ] Create a minimal test case that reproduces the bug (fails without fix, passes with fix)
- [ ] Document the conditions required for the bug to manifest
- [ ] Add comprehensive test coverage for the mapping system
- [ ] Update `update_name_column_map()` documentation to explain auto-generated mapping types

## Implementation Notes

### Investigation Approach

1. **Add detailed logging to real scenario:**
   - Instrument `update_name_column_map()`, `_augment_column_names()`, `from_flow()`
   - Log full call stack to understand where calls originate
   - Track CustomDataFrame instance IDs to see if multiple instances are involved

2. **Binary search the real config:**
   - Start with full `_referia.yml`
   - Remove specifications one by one until it stops failing
   - Identify the minimal combination that triggers the bug

3. **Compare code paths:**
   - Trace `read_vstack()` in detail
   - Compare how interface mappings propagate to specifications
   - Check if `finalize_data()` in `io.py` affects mapping order

4. **Test hypothesis about index computation:**
   - Real config has liquid-computed Name index
   - Test if compute fields on index column affect mapping order

### Files to Examine

- `lynguine/assess/data.py`: Lines 959-1102 (`from_flow` mapping logic)
- `lynguine/assess/data.py`: Lines 2947-2964 (`_finalize_df` mapping logic)  
- `lynguine/assess/data.py`: Lines 3014-3048 (`_augment_column_names`)
- `lynguine/access/io.py`: Lines 1660-1691 (`read_vstack`)
- `lynguine/access/io.py`: Lines 1484-1557 (`finalize_data`)

## Related

- **Fixed Bug:** `2025-10-09_mapping-conflict-with-identity-mappings` - The actual bug fix
- **Prior Work:** `2025-10-02_column-mapping-conflict` - Auto-generated camelCase mapping override
- **Testing Gap:** This investigation addresses our inability to test the fix properly

## Progress Updates

### 2025-10-09

Created backlog item after spending significant effort trying to create minimal reproduction. Bug was successfully fixed (verified on 214 real records) but test creation failed, indicating incomplete understanding of the mapping system's behavior in complex scenarios.

**Attempted approaches:**
- Simple vstack with add_columns
- Sources with job_title in data
- Compute fields with row_args referencing mappings
- Mixed source types (markdown, yaml, excel)
- Specification-level mappings vs interface-level

All test scenarios passed even without the fix, suggesting the real scenario has a critical condition we haven't identified.

