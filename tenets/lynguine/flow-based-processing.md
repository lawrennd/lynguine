---
id: "flow-based-processing"
title: "Flow-Based Processing"
created: "2025-10-10"
last_updated: "2025-10-10"
version: "1.0"
tags:
- tenet
- flow
- processing
- doa
---

# Flow-Based Processing

## Tenet

**Description**: lynguine implements flow-based data processing where data moves through explicit stages and transformations. All processing should follow the access-assess-address pattern, with clear data flows that can be traced and understood. Processing should be explicit and happen during flow execution, not during object construction.

**Quote**: *"Data flows through explicit stages, not hidden construction"*

**Examples**:
- Data processing happens in `from_flow()` methods, not `__init__()`
- Mappings are created during flow processing when data is actually processed
- All transformations are explicit and happen during flow execution
- Data flows are traceable and debuggable
- Processing stages are clearly separated and documented

**Counter-examples**:
- Creating mappings during object construction before data flows
- Hidden processing that happens during initialization
- Implicit behavior that occurs without explicit flow processing
- Processing that can't be traced or understood
- Mixing construction-time and flow-time behavior

**Conflicts**:
- **vs Early Availability**: When applications need data available immediately
- Resolution: Applications should handle early availability in their own layer, not expect infrastructure to provide it
- **vs User Convenience**: When users want immediate access to processed data
- Resolution: Provide clear flow-based APIs and let applications handle convenience layers

