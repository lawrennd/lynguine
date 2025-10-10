---
id: "explicit-infrastructure"
title: "Explicit Infrastructure"
created: "2025-10-10"
last_updated: "2025-10-10"
version: "1.0"
tags:
- tenet
- infrastructure
- explicit
- doa
---

# Explicit Infrastructure

## Tenet

**Description**: lynguine is a Data Oriented Architecture (DOA) infrastructure library that should be explicit, machine-understandable, and predictable. All behavior should be explicit and documented, with no implicit or "magic" behavior that could surprise users. The library should make data flows transparent and provide clear, predictable APIs that other libraries can build upon.

**Quote**: *"Show me the data flow, make everything explicit"*

**Examples**:
- Mappings are created during explicit flow processing, not automatically
- All configuration options are explicit and documented
- Error messages clearly explain what went wrong and why
- API behavior is predictable and consistent across all methods
- Data transformations are explicit and traceable

**Counter-examples**:
- Creating mappings automatically without user request
- Accepting implicit behavior from application layers
- "Magic" behavior that happens behind the scenes
- Inconsistent behavior between similar operations
- Hidden dependencies or side effects

**Conflicts**:
- **vs User Convenience**: When users want implicit behavior for ease of use
- Resolution: Provide explicit configuration options and clear defaults, but don't hide the explicit nature
- **vs Application Needs**: When applications need implicit behavior
- Resolution: Applications should handle implicit behavior in their own layer, not expect infrastructure to be implicit
