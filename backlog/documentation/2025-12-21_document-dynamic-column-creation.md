---
id: "2025-12-21_document-dynamic-column-creation"
title: "Document Dynamic Column Creation Patterns in CustomDataFrame"
status: "completed"
priority: "Medium"
created: "2025-12-21"
last_updated: "2025-12-21"
owner: ""
github_issue: ""
dependencies: "2025-12-21_implement-add-column-drop-column"
tags:
- backlog
- documentation
- usability
---

# Task: Document Dynamic Column Creation Patterns

## Description

Users need clear documentation on how to dynamically add columns to `CustomDataFrame` instances. The current behavior via `__setitem__` works but isn't well-documented, and the `add_column()` method raises `NotImplementedError`, which is confusing.

This task is to comprehensively document:
1. How to add columns using direct assignment
2. How `autocache` enables dynamic column creation
3. The difference between `colspec` types and when to use each
4. When to use the new `add_column()` method vs. direct assignment
5. Limitations and best practices

## Current Documentation Gaps

- No documentation on using `df[column] = value` pattern
- No explanation of `autocache` property and its role
- No examples of creating columns in different `colspec` types
- No guidance on when `set_value_column()` works vs. doesn't work
- The `add_column()` method shows in API docs but raises `NotImplementedError`

## Acceptance Criteria

- [x] Add section to README.md on "Working with Columns"
- [x] Document `autocache` property in API docs with examples
- [x] Add examples to `CustomDataFrame` docstring showing column creation
- [x] Create user guide section in docs/: "Column Management in CustomDataFrame"
- [x] Document all `colspec` types and their use cases
- [x] Add examples showing when to use `add_column()` vs. direct assignment
- [x] Document the limitation: `set_value_column()` requires column to exist first
- [x] Add troubleshooting section for common column-related errors
- [x] Include examples in quickstart or getting started guide
- [x] Update compute framework documentation to mention dynamic column creation

## Implementation Notes

### Suggested Documentation Structure

#### 1. README.md Addition

```markdown
### Working with Columns in CustomDataFrame

#### Adding Columns Dynamically

CustomDataFrame supports dynamic column creation through direct assignment:

\`\`\`python
import pandas as pd
from lynguine.assess.data import CustomDataFrame

# Create a basic dataframe
df = CustomDataFrame(pd.DataFrame({'A': [1, 2, 3]}, index=['a', 'b', 'c']))

# Add a new column using direct assignment
df['B'] = pd.Series([4, 5, 6], index=['a', 'b', 'c'])

# Or use the add_column() method
df.add_column('C', [7, 8, 9])

# Specify a colspec type
df.add_column('output_field', [10, 11, 12], colspec='output')
\`\`\`

New columns are automatically added to the "cache" colspec type by default, 
which makes them mutable and available for computations.
```

#### 2. User Guide: Column Management

Create `docs/column_management.md` covering:
- Introduction to colspec types
- Dynamic column creation patterns
- The `autocache` property
- Column type migration
- Best practices
- Common pitfalls

#### 3. API Documentation Updates

Add to `CustomDataFrame.__setitem__` docstring:

```python
"""
Set values for a column in the CustomDataFrame.

When setting a column that doesn't exist, it will be automatically created
in the 'cache' colspec if autocache is True (default).

Examples:
    >>> df['new_column'] = pd.Series([1, 2, 3], index=df.index)
    >>> df['another_column'] = [4, 5, 6]  # List is converted to Series
"""
```

#### 4. Troubleshooting Guide

Common issues:
- **Error**: `KeyError: 'Attempting to add column "X" as a set request has been given to non existent column'`
  - **Solution**: Use direct assignment (`df[column] = value`) or `add_column()` instead of `set_value_column()`

- **Error**: `Column already exists`
  - **Solution**: Either drop the column first or assign to it directly to replace values

### Example Code Snippets to Include

```python
# Example 1: Creating columns for compute operations
df = CustomDataFrame(pd.DataFrame({'text': ['hello', 'world']}))
df['word_count'] = None  # Pre-create column for compute to populate

# Example 2: Different colspec types
df.add_column('input_field', data, colspec='input')     # Immutable
df.add_column('output_field', data, colspec='output')   # Mutable, written to file
df.add_column('cache_field', data, colspec='cache')     # Mutable, temporary

# Example 3: Series vs non-series columns
df.add_column('regular_col', [1, 2, 3])                 # One value per row
df['series_col'] = pd.Series([1, 2, 2, 3], index=[0, 0, 1, 1])  # Multiple values per row
```

## Related

- Backlog: 2025-12-21_implement-add-column-drop-column (should be completed first)
- Documentation: README.md, docs/compute_framework.md
- Code: lynguine/assess/data.py

## Progress Updates

### 2025-12-21

Task created. Identified significant documentation gaps around dynamic column creation, `autocache`, and `colspec` types. Users currently have to discover these patterns through trial and error or by reading the source code.

### 2025-12-21 - Completion

Documentation completed with comprehensive coverage:

1. **CustomDataFrame Class Docstring** (lynguine/assess/data.py):
   - Added 57-line docstring with full API overview
   - Included examples of add_column(), drop_column(), direct assignment
   - Documented all column specification types
   - Added cross-references to related methods

2. **Column Management Guide** (docs/getting_started/column_management.rst):
   - Created comprehensive 240-line user guide
   - Explained all 5 colspec types with use cases
   - Provided two methods for adding columns with pros/cons
   - Documented common patterns (pre-creating columns, type conversion, series data)
   - Included best practices section
   - Added troubleshooting for 3 common errors with solutions
   - Integrated into docs/index.rst table of contents

3. **README.md Update**:
   - Added "Working with Columns in CustomDataFrame" section
   - Provided practical examples of add_column(), drop_column()
   - Explained all colspec types concisely
   - Linked to full ReadTheDocs documentation

All acceptance criteria met. Documentation is now discoverable in:
- API docs (class docstring, autodoc)
- User guides (column_management.rst in getting_started)
- README (quick reference with link to full docs)
- ReadTheDocs site (fully integrated)

