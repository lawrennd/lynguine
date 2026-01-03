---
category: features
created: '2025-12-22'
dependencies: CIP-0006
github_issue: null
id: 2025-12-22_template-expansion-for-column-lists
last_updated: '2025-12-22'
owner: lawrennd
priority: Medium
related_cips: []
status: Proposed
tags:
- backlog
- features
- template
- columns
- referia
- cip0006
title: Template Expansion for Column Lists
---

# Task: Template Expansion for Column Lists

## Description

Extend the template expansion system (CIP-0006) to support templated column name generation, reducing the tedium of specifying long lists of repetitive column names in `output`, `series`, and other configuration sections.

## Motivation

### Current Problem

Column specifications involve extensive repetition. For example, in thesis review configs:

```yaml
output:
  index: Name
  type: excel
  columns:
  - Author Comment
  - Summary Comment
  - Background Comment
  - Detail Comment
  - abstractGeneralComments
  - abstractDetailedComments
  - abstractSummary
  - abstractQuestions
  - abstractCustomPrompt
  - abstractCustomResponse
  - abstractIncludeHistory
  - abstractSummaryIncludeHistory
  - tocGeneralComments
  - tocDetailedComments
  - ch1GeneralComments
  - ch1DetailedComments
  - ch1Summary
  - ch1Questions
  - ch1CustomPrompt
  - ch1CustomResponse
  - ch1IncludeHistory
  - ch1SummaryIncludeHistory
  - ch2GeneralComments
  - ch2DetailedComments
  # ... repeated for ch3, ch4, ... ch12
  - refGeneralComments
  - refDetailedComments
  - appGeneralComments
  - appDetailedComments
```

This results in:
- **100+ column names** to specify manually
- **Repetitive patterns**: Each chapter has the same set of field suffixes
- **Error-prone**: Easy to miss a column or introduce typos
- **Difficult maintenance**: Adding a new field requires updating 12+ entries

### Pattern Analysis

The pattern is: `{prefix}{suffix}` where:
- **Prefixes**: `abstract`, `toc`, `ch1`, `ch2`, ... `ch12`, `ref`, `app`
- **Suffixes**: `GeneralComments`, `DetailedComments`, `Summary`, `Questions`, `CustomPrompt`, `CustomResponse`, `IncludeHistory`, `SummaryIncludeHistory`

Not all sections have all suffixes (e.g., `toc` might only have `GeneralComments` and `DetailedComments`).

### Proposed Solution

Allow templated column name generation:

```yaml
output:
  columns:
  - Author Comment
  - Summary Comment
  - Background Comment
  - Detail Comment
  - template: section_columns
    instances:
      - prefix: abstract
        suffixes: [GeneralComments, DetailedComments, Summary, Questions, CustomPrompt, CustomResponse, IncludeHistory, SummaryIncludeHistory]
      - prefix: toc
        suffixes: [GeneralComments, DetailedComments]
      - prefix: ch1
        suffixes: [GeneralComments, DetailedComments, Summary, Questions, CustomPrompt, CustomResponse, IncludeHistory, SummaryIncludeHistory]
      - prefix: ch2
        suffixes: [GeneralComments, DetailedComments, Summary, Questions, CustomPrompt, CustomResponse, IncludeHistory, SummaryIncludeHistory]
      # ... etc
```

Or even more compact using ranges:

```yaml
output:
  columns:
  - Author Comment
  - Summary Comment
  - Background Comment
  - Detail Comment
  - template: chapter_columns
    prefixes: [ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8, ch9, ch10, ch11, ch12]
    suffixes: [GeneralComments, DetailedComments, Summary, Questions, CustomPrompt, CustomResponse, IncludeHistory, SummaryIncludeHistory]
  - template: section_columns
    instances:
      - prefix: abstract
        suffixes: [GeneralComments, DetailedComments, Summary, Questions, CustomPrompt, CustomResponse, IncludeHistory, SummaryIncludeHistory]
      - prefix: toc
        suffixes: [GeneralComments, DetailedComments]
      - prefix: ref
        suffixes: [GeneralComments, DetailedComments]
      - prefix: app
        suffixes: [GeneralComments, DetailedComments]
```

This could reduce 100+ lines to ~20 lines.

## Acceptance Criteria

- [ ] Column templates can be defined inline or in external files
- [ ] Simple prefix-suffix concatenation works: `{prefix}{suffix}` → `ch1Summary`
- [ ] Can specify multiple prefixes with same suffixes (cartesian product)
- [ ] Can specify different suffixes per prefix (one-to-one or one-to-many)
- [ ] Template expansion generates flat list of column names
- [ ] Expanded columns are added to the appropriate location in column list
- [ ] Can mix explicit column names and templated columns
- [ ] Works in `output.columns`, `series.columns`, and other column lists
- [ ] Clear error messages for invalid template specifications
- [ ] Integration with review template expansion (CIP-0006)
- [ ] All tests pass
- [ ] Documentation is complete

## Implementation Notes

### Relationship to CIP-0006

This is a **specialized case** of template expansion:

- **CIP-0006**: Templates expand to complex nested structures (review UI elements)
- **This task**: Templates expand to simple lists of strings (column names)

**Options**:

1. **Shared infrastructure**: Use same template expansion mechanism
   - Pros: Consistent syntax, reuse code
   - Cons: May be overengineered for simple string concatenation

2. **Separate mechanism**: Simple string concatenation logic
   - Pros: Simpler implementation, easier to understand
   - Cons: Two template systems, inconsistent syntax

3. **Hybrid**: Share template loading, but specialized expansion for columns
   - Pros: Consistent template definition, appropriate expansion logic
   - Cons: More complex to implement

**Recommendation**: Start with **Option 2** (separate mechanism) for simplicity, then refactor to Option 3 if needed.

### Template Format

#### Simple Cartesian Product

Generate all combinations of prefixes × suffixes:

```yaml
columns:
  - template: cartesian
    prefixes: [ch1, ch2, ch3]
    suffixes: [Summary, Questions, CustomPrompt]
```

Expands to:
```
ch1Summary, ch1Questions, ch1CustomPrompt,
ch2Summary, ch2Questions, ch2CustomPrompt,
ch3Summary, ch3Questions, ch3CustomPrompt
```

#### Per-Prefix Suffixes

Different suffixes for each prefix:

```yaml
columns:
  - template: per_prefix
    instances:
      - prefix: abstract
        suffixes: [Summary, Questions]
      - prefix: toc
        suffixes: [GeneralComments]
```

Expands to:
```
abstractSummary, abstractQuestions, tocGeneralComments
```

#### With Separator

Support custom separator between prefix and suffix:

```yaml
columns:
  - template: cartesian
    prefixes: [ch1, ch2]
    suffixes: [Summary, Questions]
    separator: "_"  # default is "" (no separator)
```

Expands to:
```
ch1_Summary, ch1_Questions, ch2_Summary, ch2_Questions
```

### Implementation Location

Implement in referia's `Interface.__init__()` alongside review template expansion:

```python
class Interface(lynguine.config.interface.Interface):
    def __init__(self, data=None, directory=None, user_file=None):
        # Expand review templates (CIP-0006)
        if "templates" in data or self._has_template_references(data):
            data = self._expand_templates(data)
        
        # Expand column templates (this task)
        if self._has_column_templates(data):
            data = self._expand_column_templates(data)
        
        # Pass explicit, expanded config to lynguine
        super().__init__(data=data, directory=directory, user_file=user_file)
```

### Expansion Process

1. **Find column template references** in configuration
2. **Validate** template specification (required fields, valid types)
3. **Generate column names** based on template type:
   - Cartesian: all combinations of prefixes × suffixes
   - Per-prefix: specific suffixes for each prefix
4. **Insert** generated columns at template location
5. **Return** flat list of column names

## Technical Details

### Example Implementation

```python
def _expand_column_template(self, template_spec):
    """
    Expand a column template specification to a list of column names.
    
    Args:
        template_spec: Template specification (dict)
    
    Returns:
        List of column names (list of str)
    """
    template_type = template_spec.get('template')
    
    if template_type == 'cartesian':
        # Generate all combinations
        prefixes = template_spec['prefixes']
        suffixes = template_spec['suffixes']
        separator = template_spec.get('separator', '')
        
        columns = []
        for prefix in prefixes:
            for suffix in suffixes:
                columns.append(f"{prefix}{separator}{suffix}")
        return columns
    
    elif template_type == 'per_prefix':
        # Generate per-prefix combinations
        columns = []
        for instance in template_spec['instances']:
            prefix = instance['prefix']
            suffixes = instance['suffixes']
            separator = instance.get('separator', '')
            
            for suffix in suffixes:
                columns.append(f"{prefix}{separator}{suffix}")
        return columns
    
    else:
        raise ValueError(f"Unknown column template type: {template_type}")
```

### Error Handling

```python
# Missing required fields
if 'prefixes' not in template_spec:
    raise ValueError(
        f"Column template 'cartesian' requires 'prefixes' field"
    )

# Invalid types
if not isinstance(template_spec['prefixes'], list):
    raise ValueError(
        f"Column template 'prefixes' must be a list, got {type(template_spec['prefixes'])}"
    )

# Empty lists
if len(template_spec['prefixes']) == 0:
    log.warning("Column template 'prefixes' is empty, no columns will be generated")
```

## Estimated Effort

- **Design**: 0.5 days (template format, integration with CIP-0006)
- **Implementation**: 1 day (template expansion logic)
- **Error Handling**: 0.5 days (validation, error messages)
- **Testing**: 0.5 days (unit and integration tests)
- **Documentation**: 0.5 days (user guide, examples)

**Total**: 3 days

## Dependencies

- **CIP-0006**: Configuration Template Expansion System (design document)
- **Related**: 2025-12-22_implement-template-expansion (review template implementation)

**Note**: This can be implemented independently of review template expansion, but should use consistent syntax and approach where possible.

## Related

- **CIP**: 0006 (Configuration Template Expansion System - includes discussion of column templating)
- **Related Backlog**: 2025-12-22_implement-template-expansion (review UI template expansion - more complex case)
- **Tenet**: Explicit Infrastructure (`lynguine/tenets/lynguine/explicit-infrastructure.md`)
- **Tenet**: Flow-Based Processing (`lynguine/tenets/lynguine/flow-based-processing.md`)

## Progress Updates

### 2025-12-22
Task created with Proposed status. This extends template expansion (CIP-0006) to handle column name generation, addressing the tedium of specifying long lists of repetitive column names.

**Implementation order**: Consider implementing AFTER review template expansion (2025-12-22_implement-template-expansion) to leverage lessons learned and potentially share infrastructure.