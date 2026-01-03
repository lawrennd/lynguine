---
id: "REQ-0006"
title: "Clear Architectural Boundaries and Separation of Concerns"
created: "2026-01-03"
last_updated: "2026-01-03"
status: "Proposed"
priority: "High"
owner: "lawrennd"
stakeholders: "Development team, Application developers, Users"
related_tenets:
- explicit-infrastructure
- flow-based-processing
tags:
- requirement
- architecture
- separation-of-concerns
- doa
- maintainability
---

# Requirement: Clear Architectural Boundaries and Separation of Concerns

## Description

The system architecture needs clear separation between storage/access concerns and compute/assessment concerns to improve maintainability, testability, reduce coupling, and align with Data Oriented Architecture (DOA) principles and the access-assess-address pattern.

**Problem**: Currently, storage and compute are tightly coupled:
- Unclear boundaries make dependencies confusing
- Can't use basic data access without pulling in heavy compute dependencies (spaCy)
- Hard to test storage independently of compute
- Violates DOA principle of separating data structures from operations
- Doesn't align with access-assess-address pattern

**Desired Outcome**:
- **lynguine** (infrastructure): Storage, data structures, access-level compute (template rendering, index construction)
- **vongole** (assessment): Assessment-level compute (text analysis, aggregations, transformations)
- Clear dependency direction: vongole depends on lynguine (not vice versa)
- Applications can use just storage (lynguine) or both (lynguine + vongole)
- Better testability, maintainability, and extensibility

## Acceptance Criteria

- [ ] lynguine can be installed and used without vongole
- [ ] vongole extends lynguine's compute engine (inheritance pattern)
- [ ] Base compute infrastructure stays in lynguine (function registry, argument resolution)
- [ ] Access-level compute stays in lynguine (template rendering, index construction)
- [ ] Assessment-level compute moves to vongole (NLP, aggregations, visualizations)
- [ ] No circular dependencies
- [ ] All tests pass in both packages
- [ ] Backward compatibility maintained during transition
- [ ] Import time reduced for lynguine-only usage
- [ ] Clear documentation explaining the separation

## User Stories

**As a simple data loader**, I want to use lynguine without vongole so that I don't need to install heavy NLP dependencies for basic data access.

**As an application developer**, I want clear architectural boundaries so that I know which package to depend on for my needs.

**As a maintainer**, I want separate packages so that I can test and maintain storage and compute independently.

**As a user**, I want backward compatibility so that my existing code continues to work during the transition.

**As a contributor**, I want clear separation so that I can contribute to storage or compute without needing to understand both.

## Constraints

- Must maintain backward compatibility (6-12 month deprecation period)
- Must not break existing referia or lamd code
- Must use semantic versioning correctly
- Must provide clear migration path and tooling
- Must align with Data Oriented Architecture principles
- Must respect the access-assess-address pattern

## Implementation Notes

**Key Architectural Insight**: Not all compute can be separated from storage. There are two types:

**Access Compute** (stays in lynguine):
- **When**: During data loading and structuring
- **Purpose**: Make data accessible
- **Examples**: Template rendering (`{{familyName}}_{{givenName}}`), path resolution, column mapping
- **Dependencies**: Lightweight (liquid templates, basic string ops)

**Assessment Compute** (moves to vongole):
- **When**: After data is loaded
- **Purpose**: Transform and analyze structured data
- **Examples**: Word count, NLP, aggregations, visualizations
- **Dependencies**: Heavy (spaCy, matplotlib)

**Simplified Implementation Strategy**:
- Base compute engine stays in lynguine (includes function registry, argument resolution, three-phase processing)
- vongole simply extends lynguine.Compute and adds assessment-level functions
- No need to reimplement compute infrastructure
- Maintains existing inheritance pattern (like referia currently does)

**Tenet Alignment**:
- **Explicit Infrastructure**: Clear boundaries make architecture explicit
- **Flow-Based Processing**: Aligns with access-assess-address pattern
  - Access (lynguine): Load and structure data
  - Assess (vongole): Compute and transform data
  - Address (future): Output and presentation

**Dependency Structure**:
```
lynguine (base: storage + access compute + base engine)
    ↑
    │ depends on & extends
    │
vongole (assessment compute functions)
    ↑
    │ depends on both
    │
applications (referia, lamd, etc.)
```

## Related

- CIP: [CIP-0007](../cip/cip0007.md) (Proposed)
- Backlog Items:
  - `2025-12-22_investigate-compute-integration-for-config-sections.md` (Investigation - related)
- Tenets:
  - `explicit-infrastructure`: Separation makes architecture explicit
  - `flow-based-processing`: Aligns with access-assess-address pattern
- Related CIPs:
  - CIP-0003: Layering principles

## Implementation Status

- [x] Not Started
- [ ] In Progress
- [ ] Implemented
- [ ] Validated

## Progress Updates

### 2025-12-24

CIP-0007 proposed with comprehensive implementation plan:
- 5 phases: Preparation, Create vongole, Backward compatibility, Update downstream, Cleanup
- Estimated timeline: 3-4 months implementation + 6-12 month deprecation
- Simplified architecture: base engine stays in lynguine, vongole just extends
- Clear migration path for users and downstream projects

### 2026-01-03

Requirement created. Status: Proposed, awaiting CIP-0007 acceptance.

**Key Decision**: Keep base compute engine in lynguine
- Access compute needs the infrastructure
- Makes vongole simpler (just adds functions)
- Maintains compatibility with existing patterns
- vongole becomes a thin extension layer

**Migration Strategy**:
1. Phase 1 (0.2.x): Full backward compatibility with deprecation warnings
2. Phase 2 (6-12 months): Deprecation period with migration tools
3. Phase 3 (0.3.0): Clean architecture, stable release

**Success Criteria**:
- lynguine works standalone without vongole
- vongole extends cleanly
- Existing code works (with warnings)
- Clear documentation
- All tests pass

