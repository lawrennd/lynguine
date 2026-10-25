Server Mode (experimental)
==========================

.. warning::
   CIP-0008 is still **Proposed**. ``lynguine.client`` and ``lynguine.server`` exist on main, but server mode is not the default path and the CIP has not been accepted. Direct ``CustomDataFrame.from_flow`` is the supported interface.

A long-running process can keep lynguine loaded so repeated subprocess callers (for example ``lamd``) avoid paying import cost each time. Jupyter kernels such as ``referia`` already stay loaded; they do not need this.

Local timings from the server-mode work (one machine, not a guarantee): about 1.5s down to about 10ms on a subsequent call.

Overview
--------

**When to Use Server Mode:**

✅ Multiple lynguine calls (loops, batch processing)

✅ Subprocess-based applications (like ``lamd``)

✅ Slow startup times (~2s per call)

✅ Single-user, local development

**If you use it:**

- Auto-start, idle timeout, and retry exist on ``ServerClient``
- Intended for local, single-user, repeated subprocess calls
- Not a remote multi-user service (that is CIP-0008 Phase 4, not done)

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

CIP status
----------

CIP-0008 remains Proposed. Code for a local server/client is in the tree; remote access (auth, TLS, multi-user) is not. Do not treat the phase checklist in older notes as a closed CIP.

See Also
--------

- :doc:`/getting_started/quickstart` - General lynguine quickstart
- :doc:`/security/index` - Security and credential management
- `CIP-0008 <https://github.com/lawrennd/lynguine/blob/main/cip/cip0008.md>`_ - Full technical specification
- `REQ-0007 <https://github.com/lawrennd/lynguine/blob/main/requirements/req0007_fast-repeated-access.md>`_ - Requirements

