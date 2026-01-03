---
category: infrastructure
created: '2025-12-22'
dependencies: null
github_issue: null
id: 2025-12-22_investigate-compute-integration-for-config-sections
last_updated: '2025-12-22'
owner: lawrennd
priority: Low
related_cips: []
status: Proposed
tags:
- backlog
- infrastructure
- investigation
- design
- compute
- architecture
title: Investigate Compute Interface Integration for Configuration Sections
---

# Task: Investigate Compute Interface Integration for Configuration Sections

## Description

Investigate whether configuration sections like `editpdf`, `viewer`, `documents`, and related file operations should be reconfigured to run through the compute interface rather than as separate entities in the configuration system.

**Note**: This is an **investigation task**, not an implementation task. The goal is to explore the design space and make an informed recommendation.

## Motivation

### Current Architecture

Currently, referia has multiple separate configuration sections with their own processing logic:

```yaml
editpdf:
- sourcedirectory: $HOME/Documents/
  storedirectory: $HOME/Documents/theses/drafts/
  pages: {first: Ch1FP, last: Ch1LP}
  field: Ch1
  name: thesis_ch1

viewer:
- liquid: |
    ## {{givenName}} {{familyName}}

documents:
- type: docx
  filename: report.docx
  content: ...
```

Each section:
- Has its own processing code path
- Has its own configuration schema
- Is processed independently
- Cannot leverage compute framework features

### Compute Framework

lynguine has a general-purpose compute framework that:
- Provides function registry with signatures and default arguments
- Handles different types of arguments (direct, row, column, view, etc.)
- Supports three-phase processing (precompute, compute, postcompute)
- Has well-defined extension points
- Is documented and tested

### Questions to Investigate

1. **Architectural Consistency**: Should file operations be compute functions?
2. **Template Support**: Would compute integration naturally enable templates?
3. **Migration Path**: What would migration look like? Is it worth the breaking change?
4. **Fit Assessment**: Do these operations actually fit the compute model?
5. **Generalization**: If yes, what other sections could benefit from this pattern?

## Acceptance Criteria

- [ ] Document current architecture for `editpdf`, `viewer`, `documents`
- [ ] Analyze how these would map to compute functions
- [ ] Identify benefits and drawbacks of compute integration
- [ ] Prototype example showing what config would look like
- [ ] Assess migration complexity and breaking changes
- [ ] Make recommendation (integrate, don't integrate, or partial integration)
- [ ] Document findings in investigation report
- [ ] Create follow-up CIP or backlog tasks based on recommendation

## Investigation Scope

### Phase 1: Current State Analysis

Document how these sections currently work:

- [ ] **editpdf**: How is PDF extraction/splitting currently implemented?
  - What code processes this configuration?
  - What are the inputs and outputs?
  - What are the dependencies?

- [ ] **viewer**: How is the viewer content currently rendered?
  - How does liquid template processing work?
  - How are display elements composed?
  - What is the relationship to review?

- [ ] **documents**: How is document generation currently handled?
  - What document types are supported?
  - How does content generation work?
  - What is the rendering pipeline?

**Deliverable**: Current state documentation

### Phase 2: Compute Integration Analysis

Explore what compute integration would look like:

- [ ] Map `editpdf` operations to compute functions
  - Function signature: `extract_pdf_pages(source, output, pages, ...)`
  - Arguments: `view_args` for filenames, `row_args` for page numbers
  - Would this be cleaner or more complex?

- [ ] Map `viewer` operations to compute functions
  - Function signature: `render_viewer_element(template, data, ...)`
  - How would composition work?
  - Would this be better or worse?

- [ ] Map `documents` operations to compute functions
  - Function signature: `generate_document(type, content, ...)`
  - How would document-specific logic work?
  - Does this make sense as a compute operation?

**Deliverable**: Prototype configurations showing compute integration

### Phase 3: Template Integration Analysis

Analyze relationship to template expansion:

- [ ] Would compute integration naturally enable templates?
- [ ] Or are templates orthogonal to compute integration?
- [ ] Could we have templates WITHOUT compute integration?
- [ ] Could we have compute integration WITHOUT templates?

**Deliverable**: Analysis of template + compute interactions

### Phase 4: Trade-offs Analysis

Document benefits and drawbacks:

**Benefits**:
- [ ] Architectural consistency (everything is compute)
- [ ] Leverage existing compute infrastructure
- [ ] Natural template support through compute specs
- [ ] Reduced special-case code
- [ ] Consistent argument resolution
- [ ] Better extensibility

**Drawbacks**:
- [ ] Breaking change for existing configurations
- [ ] Migration complexity
- [ ] May force operations into wrong abstraction
- [ ] Could make simple things more complex
- [ ] May not fit all operations well

**Deliverable**: Comprehensive trade-offs document

### Phase 5: Recommendation

Based on investigation, recommend one of:

1. **Integrate**: Move these sections to compute framework
   - Create CIP for compute integration
   - Create migration backlog tasks
   - Document migration path

2. **Don't Integrate**: Keep separate sections
   - Document why compute integration doesn't fit
   - Consider templates for these sections separately
   - Keep current architecture

3. **Partial Integration**: Some sections integrate, others don't
   - Identify which sections fit compute model
   - Create selective integration plan
   - Document why some don't integrate

**Deliverable**: Recommendation with rationale

## Investigation Questions

### Architectural Questions

1. Does compute framework fit operations that:
   - Produce side effects (file creation)?
   - Don't necessarily return data to DataFrame?
   - Have complex multi-stage processing?

2. How would compute functions handle:
   - PDF extraction (input: PDF path, output: extracted PDF file)?
   - Viewer rendering (input: template, output: displayed UI)?
   - Document generation (input: config, output: Word/PDF file)?

3. What is the relationship between:
   - Compute functions and file I/O?
   - Compute functions and UI rendering?
   - Compute functions and document generation?

### Design Philosophy Questions

1. **Explicit Infrastructure**: Does compute integration make things more or less explicit?

2. **Flow-Based Processing**: Do these operations fit the flow-based processing model?

3. **Layering**: Are these infrastructure operations (lynguine) or application operations (referia)?

### Practical Questions

1. How many existing configurations would break?
2. What is the migration effort?
3. Can we provide backward compatibility?
4. What is the learning curve for users?

## Technical Details

### Example: editpdf as Compute Function

**Current configuration**:
```yaml
editpdf:
- sourcedirectory: $HOME/Documents/
  storedirectory: $HOME/Documents/theses/drafts/
  pages: {first: Ch1FP, last: Ch1LP}
  field: Ch1
  name: thesis_ch1
```

**As compute function**:
```yaml
compute:
- function: extract_pdf_pages
  field: Ch1_extracted  # or null if side-effect only
  view_args:
    source_file: "{ThesisPDF}"
    output_name: "thesis_ch1"
  row_args:
    first_page: Ch1FP
    last_page: Ch1LP
  args:
    source_directory: $HOME/Documents/
    output_directory: $HOME/Documents/theses/drafts/
```

**Questions**:
- Is this clearer or more obscure?
- Does it actually fit the compute model?
- What is gained? What is lost?

## Estimated Effort

- **Phase 1**: 1 day (current state analysis)
- **Phase 2**: 2 days (compute integration analysis and prototyping)
- **Phase 3**: 0.5 days (template integration analysis)
- **Phase 4**: 1 day (trade-offs analysis)
- **Phase 5**: 0.5 days (recommendation and documentation)

**Total**: 5 days for complete investigation

## Deliverables

1. **Investigation Report**: Comprehensive analysis document
2. **Prototype Configurations**: Example configs showing proposed integration
3. **Trade-offs Document**: Benefits vs drawbacks analysis
4. **Recommendation**: Clear recommendation with rationale
5. **Follow-up Tasks**: CIP or backlog tasks based on recommendation

## Related

- **CIP**: 0006 (Configuration Template Expansion System - mentions this investigation)
- **Compute Framework**: `lynguine/docs/compute_framework.md`
- **Tenet**: Explicit Infrastructure
- **Tenet**: Flow-Based Processing
- **Related Backlog**: 2025-12-22_implement-template-expansion

## Progress Updates

### 2025-12-22
Investigation task created. This is a design exploration to inform future architectural decisions about whether configuration sections should be integrated with the compute framework.

**Note**: This investigation should be done AFTER template expansion (CIP-0006) is implemented, as the learnings from template implementation may inform this investigation.