---
id: "2025-05-28_index-missing-from-mapping"
title: "Index column not included in mapping generation"
status: "Proposed"
priority: "High"
effort: "Medium"
type: "bug"
created: "2025-05-28"
last_updated: "2025-05-28"
owner: "lawrennd"
github_issue: null
dependencies: null
---

## Description

This assertion fails

```python
import lynguine as lg

interface = lg.config.interface.Interface.from_yaml("""input:
  type: local
  index: BGN  # index column is BGN
  select: 2032A
  data:
    - BGN: 2032A
      Title: A Project title
  mapping:
    BGN: BGN # BGN is in mapping
    Title: project_title""")
data = lg.assess.data.CustomDataFrame.from_flow(interface)
assert("BGN" in data.mapping()) # This assertion fails
```

The issue is in the `mapping()` method of `CustomDataFrame` in `data.py`. While there is a check for the index column:
```python
mapping = {name: column for name, column in self._default_mapping().items() if column in self.columns or column==self.index.name}
```
This only checks if the column name matches the index name, but doesn't actually include the index in the mapping.

## Acceptance Criteria

- [ ] Minimal example running without assertion error
- [ ] Test cases created to ensure that index error doesn't recurr
- [ ] Index column is properly included in mapping regardless of whether it's present as a DataFrame column

## Implementation Notes

### Analysis (2025-05-28)

- The index column is set as the DataFrame index and then deleted from the columns after being set, so it is not present in the columns list used to generate the mapping.
- The mapping is generated from the DataFrame columns, so the index column is excluded by design.
- This is a common pandas pattern, but for this use case, the index column should be explicitly included in the mapping.

### Decision

- The correct pattern is to explicitly add the index column to the mapping after generating it from the columns.
- This will ensure that the mapping always includes the index, regardless of whether it is present as a DataFrame column.

### Implementation Approach

1. Modify the `mapping()` method in `CustomDataFrame` to:
   - First generate the mapping from columns as currently done
   - Then explicitly add the index column to the mapping if it exists
   - Ensure the index column is added with its original name as both key and value

## Related

- Referia Issue: 2025-05-28_index-missing-from-mapping
- Documentation: [Links to relevant documentation]

## Progress Updates

### 2025-05-28

Created backlog item after identifying that the fix needs to be implemented in lynguine's `data.py` file. 