---
id: "REQ-0005"
title: "Configuration Flexibility and Maintainability"
created: "2026-01-03"
last_updated: "2026-01-03"
status: "Ready"
priority: "Medium"
owner: "lawrennd"
stakeholders: "Configuration authors, Maintainers, Application users"
related_tenets:
- explicit-infrastructure
- flow-based-processing
tags:
- requirement
- configuration
- maintainability
- DRY
- templates
---

# Requirement: Configuration Flexibility and Maintainability

## Description

Configuration files need a way to reduce repetition through reusable patterns while maintaining explicitness, traceability, and machine-understandability. Users managing complex configurations (e.g., PhD thesis reviews with 12+ chapters) need DRY (Don't Repeat Yourself) capabilities without sacrificing clarity.

**Problem**: Large configuration files contain massive repetition:
- 2700+ line files with the same 100-line pattern repeated 12+ times
- Difficult maintenance: updates require changing 12+ locations
- Error-prone: easy to miss updates or introduce inconsistencies
- Poor readability: hard to see overall structure through repetition

**Desired Outcome**:
- Template system for reusable configuration patterns
- Significant reduction in configuration file size (~50x for thesis reviews)
- Single source of truth for repeated patterns
- Maintain explicitness (templates are explicit, expansion is explicit)
- Backward compatibility (existing configurations still work)

## Acceptance Criteria

- [ ] Template definition syntax designed (inline and external file)
- [ ] Parameter substitution implemented (`{prefix}`, `{filename}`, etc.)
- [ ] Template expansion happens explicitly during flow processing
- [ ] Expanded configuration is fully explicit (lynguine never sees templates)
- [ ] Error messages are clear and actionable
- [ ] Debugging support (can inspect pre/post expansion)
- [ ] Comprehensive test coverage (100% of expansion module)
- [ ] Backward compatibility maintained (explicit configs still work)
- [ ] Migration guide for converting existing configs to templates

## User Stories

**As a configuration author**, I want to define a review pattern once and reuse it for 12 chapters so that I don't have to maintain 2700+ lines of repetitive configuration.

**As a maintainer**, I want a single source of truth for patterns so that when I need to update the review structure, I only change it in one place.

**As a reviewer**, I want compact, readable configurations so that I can understand the overall review structure without scrolling through thousands of lines.

**As a developer**, I want explicit template expansion so that I can debug issues by inspecting both the compact and expanded forms.

## Constraints

- Templates must be explicit (not inferred or guessed)
- Expansion must happen in application layer (referia), not infrastructure (lynguine)
- lynguine must receive fully expanded, explicit configuration
- Must maintain backward compatibility (no breaking changes)
- Must support mixing templates and explicit configuration
- Template expansion must be traceable and debuggable

## Implementation Notes

**Design Philosophy Alignment**:

This requirement respects both core tenets:

**Explicit Infrastructure Tenet**:
- Templates are explicitly defined
- Template references are explicit
- Expansion is explicit (happens in referia.Interface)
- Result is explicit (lynguine sees fully expanded config)
- Process is traceable (can inspect expansion)

**Flow-Based Processing Tenet**:
- Expansion happens during explicit flow processing
- Not hidden in construction or implicit preprocessing
- Part of documented data transformation flow
- Each stage is explicit and inspectable

**Architectural Layering**:
- **referia (Application)**: Implements template expansion for user convenience
- **lynguine (Infrastructure)**: Receives explicit, expanded configuration
- Clear boundary: applications provide convenience, infrastructure stays pure

**Implementation Location**: Referia, not lynguine (domain-specific convenience)

**Test-Driven Development**:
This feature MUST be developed using TDD:
1. Write tests first before implementation
2. Watch them fail (red)
3. Implement minimum code to pass (green)
4. Refactor while keeping tests green

## Related

- CIP: [CIP-0006](../cip/cip0006.md) (Proposed)
- Backlog Items:
  - `2025-12-22_implement-template-expansion.md` (Proposed)
  - `2025-12-22_template-expansion-for-column-lists.md` (Proposed - related)
  - `2025-12-22_investigate-compute-integration-for-config-sections.md` (Investigation - related architectural question)
- Tenets:
  - `explicit-infrastructure`
  - `flow-based-processing`
- Related CIPs:
  - CIP-0003: Layering principles (application vs infrastructure)

## Implementation Status

- [x] Not Started
- [ ] In Progress
- [ ] Implemented
- [ ] Validated

## Progress Updates

### 2025-12-22

CIP-0006 proposed with comprehensive design:
- Template definition format (inline and external)
- Parameter substitution syntax
- Expansion process and timing
- Error handling and debugging support
- Test-driven development approach required
- Backward compatibility strategy

### 2026-01-03

Requirement created. Status: Ready for implementation once CIP-0006 is accepted.

**Scope**:
- Initial focus: `review:` section templates
- Future consideration: `editpdf:` and other sections
- Related investigation: Should config sections be integrated with compute interface?

**Real-World Impact**:
- Current config: 2719 lines (theses/drafts/introduction/_referia.yml)
- Expected with templates: ~50 lines
- Maintenance: 1 place to update instead of 12+
- Readability: Clear overall structure visible

