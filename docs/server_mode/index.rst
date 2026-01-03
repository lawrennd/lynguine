Server Mode
===========

Lynguine Server Mode provides fast repeated access by keeping lynguine loaded in memory, avoiding the ~2 second startup cost for each call.

**Performance**: 156.3x speedup for repeated operations (1.532s → 9.8ms)

.. note::
   Server mode is designed for applications that call lynguine multiple times via subprocesses (like ``lamd``). 
   It is **not needed** for long-running processes like Jupyter kernels (``referia``).

Overview
--------

**When to Use Server Mode:**

✅ Multiple lynguine calls (loops, batch processing)

✅ Subprocess-based applications (like ``lamd``)

✅ Slow startup times (~2s per call)

✅ Single-user, local development

**Benefits:**

- **156.3x speedup** for repeated calls
- **Auto-start**: Zero setup required
- **Auto-restart**: Crash recovery
- **Auto-shutdown**: Idle timeout
- **Retry logic**: Network resilience

Quick Start
-----------

.. code-block:: python

   from lynguine.client import ServerClient

   # Zero-setup client (auto-starts server)
   client = ServerClient(
       auto_start=True,        # Starts server automatically
       idle_timeout=300,       # 5-minute timeout
       max_retries=3,          # Retry on failures
       retry_delay=1.0         # Exponential backoff
   )

   # Use just like direct mode
   df = client.read_data(interface_file='config.yml')
   client.close()

Contents
--------

.. toctree::
   :maxdepth: 2

   quickstart
   migration
   api
   troubleshooting
   examples

Performance
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 20 10

   * - Scenario
     - Direct Mode
     - Server (First)
     - Server (Subsequent)
     - Speedup
   * - Single call
     - 1.947s
     - 1.947s
     - --
     - 1x
   * - 10 calls
     - 19.47s
     - 1.947s + 98ms
     - 98ms
     - 198x
   * - 100 calls
     - 194.7s
     - 1.947s + 980ms
     - 980ms
     - 67x

Implementation Phases
---------------------

**Phase 1: Proof of Concept** ✅
   Basic server/client, instance checking, benchmarks

**Phase 2: Core Features** ✅
   New endpoints, idle timeout, auto-start, diagnostics

**Phase 3: Robustness** ✅
   Retry logic, crash recovery, comprehensive documentation

**Phase 4: Remote Access** (optional)
   Authentication, TLS, multi-user support

See Also
--------

- :doc:`/getting_started/quickstart` - General lynguine quickstart
- :doc:`/security/index` - Security and credential management
- `CIP-0008 <https://github.com/lawrennd/lynguine/blob/main/cip/cip0008.md>`_ - Full technical specification
- `REQ-0007 <https://github.com/lawrennd/lynguine/blob/main/requirements/req0007_fast-repeated-access.md>`_ - Requirements

