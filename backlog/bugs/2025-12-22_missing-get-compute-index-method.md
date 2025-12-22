---
id: "2025-12-22_missing-get-compute-index-method"
title: "Implement missing get_compute_index() method in CustomDataFrame"
status: "Completed"
priority: "High"
created: "2025-12-22"
last_updated: "2025-12-22"
owner: ""
github_issue: ""
dependencies: ""
tags:
- backlog
- bug
- compute
- critical
---

# Task: Implement missing get_compute_index() method in CustomDataFrame

## Description

The `CustomDataFrame` class is missing the `get_compute_index()` method which is called by referia's `compute_onchange()` function in `review.py`. This causes repeated errors when field widgets change values, preventing PDF generation and other compute-dependent operations from working correctly.

**Error message:**
```
ERROR:referia.util.widgets:2025-12-22 08:50:58,686:An error occurred in FieldWidget.on_value_change: 'CustomDataFrame' object has no attribute 'get_compute_index'
```

**Location of error:** `/Users/neil/lawrennd/referia/referia/assess/review.py`, line 1145

**Calling code:**
```python
def compute_onchange(self):
    if self.index is not None:
        data = self._data
        compute_index = data.get_compute_index(self.index)  # ← Missing method
        if "compute" in self._interface and data is not None:
            if compute_index is not None:
                if self.column_name is not None:
                    self._system.compute.run_onchange(data, compute_index, self.column_name)
```

**Purpose:**
The method should identify whether a given index has compute operations that need to run on change (e.g., timestamp updates, computed fields). It's used to determine if `compute.run_onchange()` should be called when a field value changes.

## Acceptance Criteria

- [x] Implement `get_compute_index(index)` method in `CustomDataFrame` class
- [x] Method returns the index if it exists in the dataframe and is valid for compute operations
- [x] Method returns `None` if the index doesn't exist or isn't valid for compute
- [x] Method handles both series and non-series type indices appropriately
- [x] Add comprehensive test suite that would have caught this missing method error
- [x] Tests cover cases with and without compute operations
- [x] Tests cover valid and invalid indices
- [x] Tests verify integration with `compute.run_onchange()`
- [x] Existing tests still pass
- [ ] Verify fix resolves PDF generation issues in referia (requires testing in referia)

## Implementation Notes

**Key insight - Why not just use `get_index()`?**

- `get_index()` (no params) → Returns the currently focused index value (`self._index`)
- `get_compute_index(index)` (takes pandas Index) → Validation gate that:
  1. Takes the **full pandas Index object** (all indices in dataframe)
  2. Validates the currently focused index is still in the Index
  3. Checks if compute operations are actually defined
  4. Returns the focused index IF valid for compute, or `None` otherwise

**Pattern in calling code:**
```python
if self.index is not None:  # Check: Does Index exist?
    compute_index = data.get_compute_index(self.index)  # Validate: Is focused index valid?
    if compute_index is not None:  # Only run if validated
        run_onchange(data, compute_index, column)
```

**Purpose:** Defensive programming - centralizes validation logic to prevent `run_onchange()` being called with stale/invalid indices or when no compute operations are defined.

**Implementation location:** `/Users/neil/lawrennd/lynguine/lynguine/assess/data.py`

**Suggested implementation:**
```python
def get_compute_index(self, index):
    """
    Validate the currently focused index for compute operations.
    
    Takes the full pandas Index object and returns the currently focused index
    if it's valid for compute operations, or None otherwise. This acts as a
    validation gate before calling compute.run_onchange().
    
    :param index: The pandas Index object containing all dataframe indices
    :type index: pd.Index
    :return: The currently focused index if valid for compute, None otherwise
    :rtype: object or None
    """
    # Get the currently focused index
    current_index = self.get_index()
    
    # If no focused index, nothing to compute
    if current_index is None:
        return None
    
    # If focused index isn't in the provided Index, invalid
    if current_index not in index:
        return None
    
    # If no compute operations defined, no need to run
    if self.compute is None or not hasattr(self.compute, '_computes') or not self.compute._computes:
        return None
    
    # Return the focused index as valid for compute
    return current_index
```

**Test scenarios:**
1. Index exists and compute is defined → return index
2. Index doesn't exist → return None
3. Compute not defined → return None
4. Empty dataframe → return None
5. Series-type indices → handle appropriately
6. Integration test with actual compute operations

## Related

- CIP: None
- PRs: None
- Error log: ~/OneDrive/referia/theses/drafts/introduction/lynguine.log (536,071 lines with repeated errors)

## Progress Updates

### 2025-12-22

Task created to address missing `get_compute_index()` method preventing PDF generation and compute operations from working correctly. Error appears hundreds of times in referia logs.

### 2025-12-22 (Completed)

Implemented `get_compute_index()` method in DataObject class:
- Added method at line 153-206 in `/Users/neil/lawrennd/lynguine/lynguine/assess/data.py`
- Method validates focused index against provided pandas Index object
- Checks if compute operations are actually defined (not just empty)
- Returns focused index if valid, None otherwise
- Created comprehensive test suite with 12 test cases in `test_get_compute_index.py`
- All tests pass (12/12)
- Existing tests still pass
- Method properly handles:
  - Valid indices with compute operations
  - No focused index
  - Invalid/stale focused indices
  - Missing or None compute attribute
  - Empty compute operations
  - Different focused indices
  - String indices
  - Empty dataframes
  - Series-type dataframes with duplicate indices
  - Integration scenario matching referia usage pattern

