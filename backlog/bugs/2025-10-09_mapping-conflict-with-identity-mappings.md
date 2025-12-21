---
id: "2025-10-09_mapping-conflict-with-identity-mappings"
title: "Mapping conflict when interface mapping overrides auto-generated identity mapping"
status: "completed"
priority: "Medium"
created: "2025-10-09"
last_updated: "2025-12-21"
owner: "lawrennd"
github_issue: null
dependencies: "CIP-0003"
tags:
- backlog
- bug
- mapping
- vstack
---

# Task: Fix mapping conflict with identity mappings

## Description

When using `vstack` to combine data from multiple sources with an interface-level mapping, the system encounters a `ValueError` when trying to override auto-generated identity mappings.

**Error scenario:**
1. A vstack combines data from multiple sources where some have a column like `job_title` (which is a valid variable name)
2. `_augment_column_names()` auto-generates an identity mapping: `job_title -> job_title`
3. The interface specifies an explicit mapping: `jobTitle: job_title`
4. When `update_name_column_map()` tries to apply the interface mapping, it raises:
   ```
   ValueError: Column "job_title" already exists in the name-column map and there's an attempt 
   to update its value to "jobTitle" when it's original value was "job_title" and that would 
   lead to unexpected behaviours.
   ```

**Root cause:**
The `update_name_column_map()` method recognizes camelCase auto-generated mappings (like `jobTitle` for `job title`) as overridable, but doesn't recognize identity mappings (like `job_title -> job_title`) as auto-generated, even though they are created automatically by `_augment_column_names()` when a column name is already a valid variable name.

**Example configuration that triggers the bug:**
```yaml
input:
  type: vstack
  index: Name
  mapping:
    givenName: given
    jobTitle: job_title  # Conflicts with auto-generated job_title -> job_title
  specifications:
  - type: markdown_directory
    source:
      - glob: "*.md"
        directory: /some/path/with/job_title/column/
  - type: yaml
    filename: data.yaml  # May or may not have job_title column
```

## Acceptance Criteria

- [ ] Interface mappings can override auto-generated identity mappings without raising ValueError
- [ ] The fix recognizes both types of auto-generated mappings:
  - [ ] Identity mappings: `column -> column` (for valid variable names)
  - [ ] CamelCase mappings: `camelCase -> column name` (for invalid variable names)
- [ ] Existing behavior for non-auto-generated mapping conflicts is preserved
- [ ] User's actual data (`~/OneDrive/referia/people/`) loads successfully

**Note on testing:** Multiple attempts to create a minimal unit test that reproduces this bug failed. The bug occurs in a complex real-world scenario with vstack combining multiple sources (markdown_directory, yaml, excel) with add_columns, compute fields, and top-level interface mappings. The fix has been validated against the actual failing scenario (214 people records) which fails without the fix and succeeds with it.

## Implementation Notes

**Solution:**
Modify the `update_name_column_map()` method in `lynguine/assess/data.py` to recognize identity mappings as auto-generated.

**Code change in `update_name_column_map()` (around line 3074):**
```python
# Before:
if original_name == auto_generated_name:
    # Allow overwriting auto-generated camelCase mappings

# After:
if original_name == auto_generated_name or original_name == column:
    # Allow overwriting both camelCase and identity auto-generated mappings
```

This simple change allows the system to recognize that when `original_name == column` (identity mapping), it's an auto-generated mapping that can be safely overridden by an explicit interface mapping.

**Why this works:**
- `_augment_column_names()` creates identity mappings for columns with valid variable names
- These are just as "auto-generated" as camelCase mappings
- Interface-level mappings should take precedence over any auto-generated mappings
- Non-auto-generated conflicts (where two different explicit names map to the same column) should still raise an error

## Related

- **Related Backlog Items:**
  - `2025-10-02_column-mapping-conflict`: This fix extends that work, which introduced the ability to override auto-generated camelCase mappings. The current fix adds recognition for identity mappings as another type of auto-generated mapping.
  - `2025-05-28_index-missing-from-mapping`: Related to mapping system behavior with index columns
  
- **Code Files:**
  - `lynguine/assess/data.py`, method `update_name_column_map()` (line ~3063-3084)
  - `lynguine/assess/data.py`, method `_augment_column_names()` (line ~3014-3048)
  - `lynguine/assess/data.py`, method `from_flow()` (line ~1098-1102)
  - Test file: `lynguine/tests/test_assess_data.py`

## Progress Updates

### 2025-10-09

Bug identified when loading `~/OneDrive/referia/people/_referia.yml` with vstack containing multiple sources and `jobTitle: job_title` mapping in the interface. Solution identified and implemented: recognize identity mappings as auto-generated by checking if `original_name == column` in addition to checking if `original_name == auto_generated_name`.

### 2025-10-10

**Test successfully created:** `lynguine/tests/test_identity_mapping_referia.py`

The key to reproducing the bug was understanding that it only occurs when using `referia`'s `CustomDataFrame`, which calls `_augment_column_names()` in `__init__`. The test patches `lynguine`'s `CustomDataFrame` to replicate this behavior.

Fix verified:
- Test PASSES with fix (identity mappings can be overridden)
- Test FAILS without fix (ValueError about conflicting mappings)
- Real scenario works correctly with 214 people loaded

Related investigation task (`2025-10-09_investigate-mapping-test-failure.md`) completed.

### 2025-12-21 - Workaround Status

**Current Status**: Workaround implemented in referia, not lynguine

After investigation, it was determined that:
1. The bug originates from referia's `__init__` calling `_augment_column_names()` early
2. lynguine remains strict (does not allow mapping overrides)
3. referia implements the workaround in its own `update_name_column_map()` override

**Workaround Location**: `referia/assess/data.py` lines 210-238
- referia's `update_name_column_map()` allows overwriting "default mappings"
- Uses `_is_default_mapping()` to identify identity and camelCase mappings
- Maintains lynguine's strict behavior for non-default mappings

**Proper Fix**: Would require implementing CIP-0003 / CIP-0005 (move augmentation to `from_flow()`)

**Status Change**: Changed from "High Priority" to "Medium Priority" and marked as "workaround_implemented" since the issue is functional but not architecturally ideal.

### 2025-12-21 - Completed via CIP-0003 Implementation

**Proper Fix Implemented**: CIP-0003 / CIP-0005 fully implemented in referia

The architectural fix has been completed:
- referia's `__init__` no longer calls `_augment_column_names()` early
- referia's `from_flow()` override applies augmentation AFTER parent completes
- Explicit interface mappings are applied BEFORE augmentation
- Timing conflict resolved at architectural level ✅

**Implementation Location**: `referia/assess/data.py`
- Line 178-180: Removed early augmentation from `__init__`
- Lines 241-266: Added `from_flow()` override with proper timing

**Result**: 
- No more timing conflicts between identity and interface mappings
- Workaround in `update_name_column_map()` remains as defensive programming
- Issue completely resolved

**Status**: Marked as "completed" - proper architectural fix implemented.

