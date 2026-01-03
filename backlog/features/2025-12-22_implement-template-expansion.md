---
category: features
created: '2025-12-22'
dependencies: CIP-0006
github_issue: null
id: 2025-12-22_implement-template-expansion
last_updated: '2025-12-22'
owner: lawrennd
priority: Medium
related_cips: []
status: Proposed
tags:
- backlog
- features
- template
- referia
- cip0006
title: Implement Configuration Template Expansion System
---

# Task: Implement Configuration Template Expansion System

## Description

Implement the template expansion system described in CIP-0006 to reduce repetition in referia configuration files. This system will allow users to define reusable patterns (templates) that can be instantiated with different parameters, dramatically reducing configuration file size and improving maintainability.

**Target**: Reduce PhD thesis review configurations from 2700+ lines to ~50 lines while maintaining full functionality.

## Motivation

### Problem

Current PhD thesis review configurations contain massive repetition:

- Same 100+ line pattern repeated for each chapter
- 12+ chapters = 1200+ lines of repetitive configuration
- Difficult to maintain (changes require updating 12+ locations)
- Error-prone (easy to miss updates or introduce inconsistencies)
- Poor readability (hard to see overall structure)

### Solution

Template expansion system that:

- Defines patterns once
- Instantiates with different parameters
- Expands during referia's Interface initialization
- Passes explicit configuration to lynguine
- Maintains design philosophy (explicit, traceable, no magic)

## Acceptance Criteria

- [ ] Templates can be defined inline in configuration files
- [ ] Templates can be loaded from external files
- [ ] Parameter substitution works correctly (`{prefix}`, `{filename}`, etc.)
- [ ] Template expansion happens in referia's `Interface.__init__()`
- [ ] lynguine receives fully expanded, explicit configuration
- [ ] Clear error messages for missing templates, parameters, or invalid structure
- [ ] DEBUG logging shows expansion process
- [ ] Option to dump expanded configuration for inspection
- [ ] Existing explicit configurations continue to work unchanged
- [ ] Can mix templates and explicit configuration
- [ ] All tests pass
- [ ] Documentation is complete

## Implementation Notes

### Test-Driven Development Mandate

**This feature MUST be developed using Test-Driven Development (TDD).**

**TDD Cycle**:
1. **Red**: Write a failing test for the next small piece of functionality
2. **Green**: Write the minimum code to make the test pass
3. **Refactor**: Clean up code while keeping tests green

**Why TDD for this feature?**:
- Template expansion is **core infrastructure** that must be robust
- TDD ensures **comprehensive test coverage** from day one
- Tests serve as **executable specification** of behaviour
- Makes **refactoring safer** as complexity grows
- Aligns with lynguine's **explicit, predictable** design philosophy
- Catches **edge cases early** (missing params, malformed templates, etc.)

**Test Organization**: See CIP-0006 for detailed test structure and coverage requirements.

### Phase 1: Core Template System with TDD (High Priority)

**Goal**: Basic template expansion working, developed using Test-Driven Development

**TDD Approach**: Write tests first, implement to make them pass, then refactor.

Tasks:
- [ ] Design template definition format (inline and external)
- [ ] **TDD: Template Loading**
  - [ ] Write tests for inline template loading
  - [ ] Write tests for external template loading
  - [ ] Write tests for error cases (missing file, malformed YAML)
  - [ ] Implement template loader to pass tests
  - [ ] Refactor if needed
- [ ] **TDD: Parameter Substitution**
  - [ ] Write tests for simple substitution (`{prefix}` → `ch1`)
  - [ ] Write tests for nested substitution (`{prefix}Summary` → `ch1Summary`)
  - [ ] Write tests for error cases (missing parameters)
  - [ ] Write tests for edge cases (empty values, special chars)
  - [ ] Implement substitution to pass tests
  - [ ] Refactor if needed
- [ ] **TDD: Template Expansion**
  - [ ] Write tests for single instance expansion
  - [ ] Write tests for multiple instances
  - [ ] Write tests for error cases (invalid templates)
  - [ ] Implement expansion logic to pass tests
  - [ ] Refactor if needed
- [ ] **TDD: Interface Integration**
  - [ ] Write tests for `Interface.__init__()` integration
  - [ ] Write tests for passing to lynguine
  - [ ] Implement integration to pass tests
  - [ ] Refactor if needed

**Deliverable**: Working template expansion with comprehensive unit test coverage

### Phase 2: Error Handling and Debugging (Medium Priority)

**Goal**: Production-ready error handling and debugging tools

Tasks:
- [ ] Add comprehensive error handling
  - [ ] Missing template definition
  - [ ] Missing required parameters
  - [ ] Invalid template structure
  - [ ] Circular template references
  - [ ] Type mismatches
- [ ] Add debugging support
  - [ ] DEBUG logging for expansion process
  - [ ] Option to dump expanded configuration
  - [ ] Clear indication when templates are used
  - [ ] Show which templates were expanded
- [ ] Add validation
  - [ ] Validate expanded configuration
  - [ ] Check for required fields
  - [ ] Verify parameter substitution is complete

**Deliverable**: Robust, debuggable template system

### Phase 3: Advanced Features (Low Priority)

**Goal**: Enhanced functionality for complex use cases

Tasks:
- [ ] Support nested templates (templates using templates)
- [ ] Support conditional expansion (if/else in templates)
- [ ] Support loops in templates (for generating sequences)
- [ ] Support template inheritance (extend base templates)
- [ ] Support default parameter values
- [ ] Support parameter validation (types, ranges, etc.)

**Deliverable**: Advanced template features for power users

### Phase 4: Integration and Regression Testing (High Priority)

**Goal**: Verify system works end-to-end with real configurations

**Note**: Unit tests written in Phase 1 (TDD). This phase adds integration and regression tests.

Tasks:
- [ ] **Integration tests**
  - [ ] Full configuration expansion with multiple templates
  - [ ] Integration with lynguine Interface (receives explicit config)
  - [ ] Real-world thesis review configurations
  - [ ] Mixed template and explicit review entries
  - [ ] Multiple template types in one config
- [ ] **Validation tests**
  - [ ] Expanded configuration is valid lynguine config
  - [ ] All required fields present
  - [ ] No template artifacts remain (`template:`, `instances:`)
  - [ ] Parameter substitution is complete (no `{...}`)
- [ ] **Regression tests**
  - [ ] Test against `theses/drafts/introduction/_referia.yml` (2719 lines)
  - [ ] Test against `theses/examined/introduction/_referia.yml` (3564 lines)
  - [ ] Verify expanded config produces same UI as explicit config
  - [ ] No functional differences in behaviour

**Deliverable**: Full system validation with regression coverage

### Phase 5: Documentation (High Priority)

**Goal**: Complete user and developer documentation

Tasks:
- [ ] User documentation
  - [ ] How to define templates
  - [ ] How to use templates
  - [ ] Parameter substitution syntax
  - [ ] Examples for common patterns
  - [ ] Troubleshooting guide
- [ ] Developer documentation
  - [ ] Template expansion architecture
  - [ ] Implementation details
  - [ ] Extension points
  - [ ] Design philosophy alignment
- [ ] Migration guide
  - [ ] Converting existing configurations
  - [ ] Best practices for template design
  - [ ] When to use templates vs explicit config
- [ ] Example templates
  - [ ] Chapter review template
  - [ ] Section review template
  - [ ] Custom query template

**Deliverable**: Complete documentation

### Phase 6: Migration (Optional, Low Priority)

**Goal**: Migrate existing configurations to use templates

Tasks:
- [ ] Create standard templates for common patterns
  - [ ] Chapter review template
  - [ ] Section review template
  - [ ] Appendix review template
- [ ] Migrate thesis review configurations
  - [ ] `theses/drafts/introduction/_referia.yml`
  - [ ] `theses/examined/introduction/_referia.yml`
  - [ ] Other thesis review configurations
- [ ] Validate migrated configurations
  - [ ] Expanded config matches original
  - [ ] All functionality preserved
  - [ ] No regressions

**Deliverable**: Migrated configurations demonstrating benefits

## Technical Details

### Template Definition Format

```yaml
templates:
  chapter_review:
    file: ../templates/chapter_review.yml
    # Or inline:
    pattern:
      - type: Checkbox
        field: {prefix}SummaryIncludeHistory
        # ... rest of pattern
```

### Template Usage

```yaml
review:
  - template: chapter_review
    instances:
      - prefix: ch1
        filename: "{Name}_thesis_ch1.pdf"
      - prefix: ch2
        filename: "{Name}_thesis_ch2.pdf"
```

### Implementation Location

```python
# In referia/config/interface.py
class Interface(lynguine.config.interface.Interface):
    def __init__(self, data=None, directory=None, user_file=None):
        # Expand templates before passing to lynguine
        if "templates" in data or self._has_template_references(data):
            data = self._expand_templates(data)
        
        # Pass explicit, expanded config to lynguine
        super().__init__(data=data, directory=directory, user_file=user_file)
```

## Dependencies

- **CIP-0006**: Configuration Template Expansion System (design document)

## Estimated Effort

**Note**: TDD approach means testing is integrated into each phase, not separate.

- **Phase 1**: 3-4 days (core functionality with TDD - includes unit test writing)
- **Phase 2**: 1-2 days (error handling and debugging with tests)
- **Phase 3**: 2-3 days (advanced features with tests, optional)
- **Phase 4**: 1-2 days (integration and regression testing)
- **Phase 5**: 1-2 days (documentation)
- **Phase 6**: 1 day (migration, optional)

**Total**: 8-15 days (depending on which phases are implemented)

**TDD Impact**: Slightly longer development time (writing tests first) but:
- Higher quality code
- Fewer bugs in production
- Easier refactoring
- Tests serve as documentation
- Overall faster to working, robust feature

## Related

- **CIP**: 0006 (Configuration Template Expansion System)
- **Tenet**: Explicit Infrastructure (`lynguine/tenets/lynguine/explicit-infrastructure.md`)
- **Tenet**: Flow-Based Processing (`lynguine/tenets/lynguine/flow-based-processing.md`)
- **Related CIP**: 0003 (Consistent Mapping Initialization - layering principles)
- **Related Backlog**: 2025-12-22_template-expansion-for-column-lists (simpler column name templating)
- **Related Backlog**: 2025-12-22_investigate-compute-integration-for-config-sections (potential integration of editpdf, viewer, etc. with compute framework)

## Progress Updates

### 2025-12-22
Task created with Proposed status. CIP-0006 and design documentation completed.