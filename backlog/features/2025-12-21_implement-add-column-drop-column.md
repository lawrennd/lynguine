---
category: features
created: '2025-12-21'
dependencies: ''
github_issue: ''
id: 2025-12-21_implement-add-column-drop-column
last_updated: '2025-12-21'
owner: ''
priority: Medium
related_cips: []
status: Completed
tags:
- backlog
- api
- usability
- features
title: Implement add_column() and drop_column() Methods in CustomDataFrame
---

# Task: Implement add_column() and drop_column() Methods

## Description

The `CustomDataFrame` class inherits `add_column()` and `drop_column()` methods from the `DataObject` base class, but these methods currently only raise `NotImplementedError`. This is confusing for users who see these methods in the API documentation but cannot use them.

The functionality for adding columns already exists via the `__setitem__` method (e.g., `df['new_col'] = data`), but this isn't exposed as a convenient method. Similarly, dropping columns should be straightforward to implement.

This task is to implement both methods properly as convenience wrappers around existing functionality.

## Current Behavior

```python
# This works but isn't intuitive
df['new_column'] = pd.Series([1, 2, 3], index=df.index)

# This raises NotImplementedError
df.add_column('new_column', pd.Series([1, 2, 3], index=df.index))

# This raises NotImplementedError
df.drop_column('old_column')
```

## Acceptance Criteria

- [x] `add_column(column_name, data, colspec='cache')` method implemented
- [x] Method properly uses existing `__setitem__` functionality
- [x] Optional `colspec` parameter to specify column type (default: 'cache')
- [x] Proper error handling for invalid column names or data
- [x] `drop_column(column_name)` method implemented
- [x] Method properly removes column from both `_d` and `_colspecs`
- [x] Comprehensive unit tests for both methods
- [x] Tests cover edge cases (existing columns, non-existent columns, different colspec types)
- [x] Docstrings updated with examples
- [x] Methods work correctly with all supported data types (Series, arrays, lists)

## Implementation Notes

### add_column() Implementation

```python
def add_column(self, column_name, data, colspec='cache'):
    """
    Add a new column to the CustomDataFrame.
    
    :param column_name: The name of the new column.
    :type column_name: str
    :param data: The data for the new column (pd.Series, list, or array).
    :type data: pd.Series, list, or array-like
    :param colspec: The column specification type (default: 'cache').
    :type colspec: str
    :raises ValueError: If column already exists or data is incompatible.
    
    Example:
        >>> df.add_column('new_col', pd.Series([1, 2, 3], index=df.index))
        >>> df.add_column('output_col', [1, 2, 3], colspec='output')
    """
    if column_name in self.columns:
        raise ValueError(f"Column '{column_name}' already exists")
    
    # Use existing __setitem__ functionality
    self[column_name] = data
    
    # If a specific colspec was requested and it's not 'cache',
    # move the column to the correct colspec
    if colspec != 'cache' and colspec in self.types:
        # Remove from cache
        if 'cache' in self._colspecs and column_name in self._colspecs['cache']:
            self._colspecs['cache'].remove(column_name)
        # Add to requested colspec
        if colspec not in self._colspecs:
            self._colspecs[colspec] = []
        self._colspecs[colspec].append(column_name)
```

### drop_column() Implementation

```python
def drop_column(self, column_name):
    """
    Drop a column from the CustomDataFrame.
    
    :param column_name: The name of the column to drop.
    :type column_name: str
    :raises KeyError: If column doesn't exist.
    
    Example:
        >>> df.drop_column('unwanted_col')
    """
    if column_name not in self.columns:
        raise KeyError(f"Column '{column_name}' not found")
    
    # Find which colspec contains this column
    col_type = self.get_column_type(column_name)
    
    # Remove from the appropriate dataframe
    if col_type in self._d:
        self._d[col_type] = self._d[col_type].drop(columns=[column_name])
    
    # Remove from colspecs
    if col_type in self._colspecs and column_name in self._colspecs[col_type]:
        self._colspecs[col_type].remove(column_name)
```

## Related

- Issue discovered during: mode parameter implementation and testing
- Related to: CustomDataFrame API design
- Documentation: Should be added to user guide

## Progress Updates

### 2025-12-21 - Completed

**Implementation Complete**: Both methods fully implemented and tested

**Changes Made**:
1. ✅ **Implemented `add_column()` method** (lynguine/assess/data.py lines ~3560-3604)
   - Wraps existing `__setitem__` functionality
   - Supports optional `colspec` parameter to specify column type
   - Validates column doesn't already exist
   - Validates colspec is valid type
   - Properly moves column to requested colspec if needed

2. ✅ **Implemented `drop_column()` method** (lynguine/assess/data.py lines ~3606-3628)
   - Removes column from internal data storage (`_d`)
   - Removes column from column specifications (`_colspecs`)
   - Validates column exists before dropping

3. ✅ **Comprehensive Test Suite** (lynguine/tests/test_add_drop_column.py)
   - 13 tests covering all functionality
   - All tests passing ✅
   - Coverage includes: basic operations, error handling, different colspecs, edge cases

**Test Results**: 13 passed in 1.52s

**Status**: Feature complete and ready for use. The `add_column()` and `drop_column()` methods now provide convenient, documented ways to add and remove columns from CustomDataFrame instances.

### 2025-12-21 - Created

Task created. Identified that `add_column()` and `drop_column()` exist in API but raise `NotImplementedError`, while the functionality already exists via `__setitem__`. Proposed implementation as convenience methods.