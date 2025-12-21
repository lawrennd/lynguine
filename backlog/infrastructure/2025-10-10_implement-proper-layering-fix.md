---
id: "2025-10-10_implement-proper-layering-fix"
title: "Implement proper layering fix for mapping initialization timing conflict"
status: "completed"
priority: "Medium"
created: "2025-10-10"
last_updated: "2025-12-21"
owner: "lawrennd"
github_issue: null
dependencies: "CIP-0003"
tags:
- backlog
- infrastructure
- mapping
- layering
- cip0003
---

# Task: Implement proper layering fix for mapping initialization timing conflict

## Description

Implement the correct architectural solution for the mapping initialization timing conflict by properly separating concerns between lynguine (infrastructure) and referia (application) layers.

**Current Problem**: The fix was applied in lynguine (infrastructure) to accept referia's implicit behavior, which made the conflation worse. Both layers are now implicit.

**Correct Solution**: 
- **lynguine**: Stay strict and explicit (revert the fix)
- **referia**: Handle implicit behavior explicitly by overriding `update_name_column_map()`

## Motivation

### Design Philosophy Tension

- **lynguine (DOA Infrastructure)**: Should be explicit, machine-understandable, flow-based processing
- **referia (User-Oriented Application)**: Should provide implicit, human-friendly convenience

### Current State (Wrong)

1. **lynguine**: Now accepts implicit behavior (identity mapping override)
2. **referia**: Still has implicit behavior
3. **Result**: Both layers are now implicit, conflation is worse

### Desired State (Correct)

1. **lynguine**: Strict and explicit (no implicit overrides)
2. **referia**: Handles implicit behavior explicitly (override method)
3. **Result**: Clear separation of concerns, proper layering

## Implementation Plan

### Phase 1: Revert lynguine fix (Low risk)
- [x] Revert `lynguine/assess/data.py` line 3071 to strict behavior
- [x] Remove identity mapping override logic from lynguine
- [x] Ensure lynguine is strict for all mapping conflicts
- [x] Update tests to reflect strict behavior

### Phase 2: Verify referia handles implicit behavior (Medium risk)
- [x] Ensure referia implements proper override in `update_name_column_map()`
- [x] Verify referia handles default mapping overrides (implicit behavior)
- [x] Verify referia reuses lynguine's strict logic for non-default cases
- [x] Test integration between layers

### Phase 3: Documentation (Low risk)
- [ ] Update CIP-0003 to reflect new approach
- [ ] Document the proper layering separation
- [ ] Explain when to use lynguine vs referia behavior

## Technical Details

### lynguine Implementation (Revert to Strict)

```python
# In lynguine's CustomDataFrame.update_name_column_map()
def update_name_column_map(self, name, column):
    """
    Strict, explicit mapping management.
    No implicit overrides allowed.
    """
    if column in self._column_name_map and self._column_name_map[column] != name:
        original_name = self._column_name_map[column]
        errmsg = f"Column \"{column}\" already exists in the name-column map and there's an attempt to update its value to \"{name}\" when it's original value was \"{original_name}\" and that would lead to unexpected behaviours."
        log.error(errmsg)
        raise ValueError(errmsg)
    
    self._name_column_map[name] = column
    self._column_name_map[column] = name
```

## Acceptance Criteria

- [x] lynguine is strict for all mapping conflicts
- [x] No implicit behavior in lynguine
- [x] referia handles implicit behavior in its own layer
- [x] Clear separation of concerns
- [x] All existing tests pass
- [x] New tests verify strict behavior

**Note**: Acceptance criteria met via workaround, not via proper architectural fix described in this backlog item.

## Related

- **CIP**: 0003 (Consistency in CustomDataFrame Initialization and Mapping Augmentation)
- **Related referia CIP**: 0005 (Fix Mapping Initialization Timing Conflict with lynguine)
- **Related referia backlog**: 2025-10-10_implement-proper-layering-fix

## Progress Updates

### 2025-12-21 - Deferred (Workaround Sufficient)

**Status Update**: Changed to "deferred" with priority lowered to "Low"

The acceptance criteria have been met, but through a workaround rather than the proper architectural fix:

1. ✅ **lynguine is strict**: No changes made to lynguine, remains strict for all mapping conflicts
2. ✅ **referia handles implicit behavior**: Implemented via `update_name_column_map()` override
3. ✅ **Clear separation**: lynguine = strict infrastructure, referia = convenient application layer

**Workaround Details**:
- Location: `referia/assess/data.py` lines 210-238
- Method: Override `update_name_column_map()` to allow default mapping overrides
- Result: Functional but not the ideal architecture described in CIP-0003

**Proper Fix (Deferred)**:
The ideal solution described in CIP-0003 would move `_augment_column_names()` from referia's `__init__` to `from_flow()` override. This remains unimplemented but deferred as the workaround is sufficient for current needs.

**Decision**: Defer proper architectural fix unless/until timing issues resurface or architectural clarity becomes critical.

### 2025-12-21 - Completed via CIP-0003 Implementation

**Proper Architectural Fix Implemented**: Changed status from "deferred" to "completed"

The proper layering fix described in CIP-0003 has been fully implemented in referia:

1. ✅ **lynguine remains strict**: No changes to lynguine, maintains explicit behavior
2. ✅ **referia handles timing correctly**: 
   - Removed early `_augment_column_names()` from `__init__`
   - Added `from_flow()` override that augments AFTER parent processes interface
3. ✅ **Clear separation of concerns**: 
   - lynguine = strict infrastructure
   - referia = convenient application layer with proper timing

**Implementation**: CIP-0003 Option B implemented via referia's CIP-0005
- Location: `referia/assess/data.py` lines 178-180 (removal), 241-266 (override)
- Result: Explicit interface mappings applied before augmentation
- Timing conflict resolved architecturally ✅

**Workaround Status**: The `update_name_column_map()` workaround remains as defensive programming but is no longer strictly necessary.

**Status**: Marked as "completed" - proper architectural layering achieved.

### 2025-10-10
Task created with Proposed status. Identified the need for proper architectural layering fix.
