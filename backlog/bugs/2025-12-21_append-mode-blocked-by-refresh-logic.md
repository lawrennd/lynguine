---
category: bugs
created: '2025-12-21'
dependencies: ''
github_issue: ''
id: 2025-12-21_append-mode-blocked-by-refresh-logic
last_updated: '2025-12-21'
owner: ''
priority: High
related_cips: []
status: Completed
tags:
- backlog
- bug
- compute
- critical
title: Append/Prepend Modes Blocked by Refresh Logic
---

# Task: Append/Prepend Modes Blocked by Refresh Logic

**Status**: Proposed  
**Priority**: High  
**Created**: 2025-12-21  
**Last Updated**: 2025-12-21

## Description

The compute system's append and prepend modes fail to execute when a field already contains content and `refresh=False` (the default). This is a critical bug that prevents the core use case for these modes: accumulating multiple results in a single field.

**Root Cause:**

In `lynguine/assess/compute.py` line 406, the condition for writing values is:

```python
if refresh or missing_val and data.ismutable(column):
```

Due to operator precedence, this evaluates as:
```python
if refresh or (missing_val and data.ismutable(column)):
```

When a field already has content:
- `refresh` defaults to `False`
- `missing_val` is `False` (field is not missing)
- Result: The entire condition is `False`, so the write never happens

**Impact:**

- Append mode cannot add to existing content (the primary use case!)
- Prepend mode cannot add to existing content
- Users must explicitly set `refresh=True` to work around the bug
- This defeats the purpose of the `missing_val` optimization

## Acceptance Criteria

- [x] Identify the root cause (line 406 logic error)
- [x] Fix the conditional logic to allow append/prepend writes even when field has content
- [x] Ensure replace mode still respects `refresh` and `missing_val` optimization
- [x] Add regression test that catches this specific bug
- [x] Verify all existing tests still pass
- [ ] Test with real-world referia workflow (multiple appends to same field)

## Implementation Notes

### The Fix

Change line 406 from:
```python
if refresh or missing_val and data.ismutable(column):
```

To:
```python
if (refresh or missing_val or mode in ["append", "prepend"]) and data.ismutable(column):
```

**Rationale:**
- Append/prepend modes **must** read existing content to work correctly
- They should always execute (like `refresh=True`), regardless of whether field is empty
- Replace mode should continue to respect the `refresh` and `missing_val` optimization
- The fix explicitly checks the mode and bypasses the optimization for accumulating modes

### Alternative Fix (More Explicit)

```python
# Always write for append/prepend modes, respect refresh/missing_val for replace
should_write = (
    (mode in ["append", "prepend"]) or  # Accumulating modes always write
    refresh or                           # Explicit refresh requested
    missing_val                          # Field is empty
)

if should_write and data.ismutable(column):
    # Apply write mode logic
    ...
```

This is more readable and makes the intent clearer.

### Test Case to Add

```python
def test_append_to_non_empty_field_without_refresh():
    """
    Regression test for bug where append mode fails on non-empty fields.
    
    This is the primary use case for append mode: adding to existing content.
    Without this fix, append only works with refresh=True, defeating the purpose.
    """
    data = CustomDataFrame()
    data.set_value_column("First entry", "notes")
    
    # Create compute config WITHOUT refresh flag
    compute = {
        "function": lambda data: "Second entry",
        "field": "notes",
        "mode": "append",
        "separator": "\n---\n"
    }
    
    compute_obj = Compute.from_flow({"compute": [compute]})
    compute_obj.run(data, interface)
    
    result = data.get_value_column("notes")
    
    # This should work WITHOUT setting refresh=True
    assert "First entry" in result
    assert "Second entry" in result
    assert "\n---\n" in result
    assert result == "First entry\n---\nSecond entry"
```

## Related

- Feature: 2025-12-21_implement-mode-parameter-compute (this bug blocks that feature)
- CIP: lynguine CIP for mode parameter implementation
- Referia: All append mode functionality depends on this fix

## Progress Updates

### 2025-12-21 - Bug Discovered

Bug discovered during testing planning. User asked: "Does the code fail to update the box if it has something in there already ... even if the mode is append?"

Investigation revealed:
1. The condition on line 406 uses incorrect operator precedence
2. `missing_val` is `False` for non-empty fields (correct)
3. Default `refresh=False` combined with operator precedence causes the write to be skipped
4. This breaks the primary use case for append/prepend modes

Priority set to **High** because:
- Blocks all append/prepend functionality in referia
- Affects core feature (conversation history accumulation)
- Simple one-line fix with clear test case
- Must be fixed before referia can use the new modes

### 2025-12-21 - Bug Fixed

**Fix Implemented:**

The bug was actually in TWO places, not just line 406:

1. **Line 380** (the earlier check): The condition `if refresh or any(missing_vals):` prevented the compute function from even running when `refresh=False` and the field had content. Fixed by adding mode check: `should_run = refresh or any(missing_vals) or mode in ["append", "prepend"]`

2. **Line 406** (the write check): The condition `if refresh or missing_val and data.ismutable(column):` prevented the write from happening. Fixed with explicit logic: `should_write = (mode in ["append", "prepend"]) or refresh or missing_val`

**Tests Updated:**

- Fixed `test_append_to_non_empty_field_without_refresh()` - renamed and updated to test the correct behavior (append should work without `refresh=True`)
- Added `test_prepend_to_non_empty_field_without_refresh()` - parallel test for prepend mode
- Fixed test fixtures to use `colspecs="cache"` instead of immutable input columns

**Test Results:**

- All 16 compute mode tests pass ✅
- All 35 compute tests pass ✅
- All 552 tests pass ✅

**Status:** Bug fixed and regression tests added. Ready for referia integration.