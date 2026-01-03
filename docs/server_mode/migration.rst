Migration Guide
===============

This guide helps you migrate from direct lynguine calls to server mode for faster repeated access.

Who Should Use Server Mode?
----------------------------

Server mode is beneficial if you:

✅ **Call lynguine multiple times** (e.g., in loops, batch processing)

✅ **Experience slow startup times** (~2 seconds per call)

✅ **Use subprocesses** to call lynguine (like ``lamd`` does)

✅ **Work in single-user, local development** environments

❌ Server mode is **NOT needed** if you:

- Already have a long-running process (e.g., Jupyter kernel)
- Only call lynguine once
- Need multi-user authentication (use Phase 4 instead)

Migration Steps
---------------

Step 1: Understand the Performance Gain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before (Direct Mode)**:

.. code-block:: python

   # Every call incurs ~2s startup (pandas, numpy, lynguine loading)
   for i in range(10):
       df = some_lynguine_call()  # 2s each = 20s total

**After (Server Mode)**:

.. code-block:: python

   # First call: ~2s startup
   # Subsequent calls: ~10ms each
   for i in range(10):
       df = client.read_data(...)  # 10ms each = ~100ms total for 9 calls

**Speedup**: 156.3x for repeated calls (1.532s → 9.8ms)

Step 2: Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Server mode requires the ``requests`` library:

.. code-block:: bash

   pip install requests

Step 3: Choose Your Migration Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Option A: Manual Server Start (Simple, Full Control)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Best for**: Development, testing, understanding the system

**Old code (direct mode)**:

.. code-block:: python

   from lynguine.access import io

   df = io.read('config.yml', directory='.')

**New code (server mode - manual)**:

.. code-block:: python

   from lynguine.client import ServerClient

   # 1. Start server in separate terminal:
   #    python -m lynguine.server

   # 2. Use client instead of direct calls
   client = ServerClient('http://127.0.0.1:8765')
   df = client.read_data(interface_file='config.yml', directory='.')
   client.close()

Option B: Auto-Start (Recommended, Zero Setup)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Best for**: Production, CI/CD, seamless integration

**Old code (direct mode)**:

.. code-block:: python

   from lynguine.access import io

   df = io.read('config.yml', directory='.')

**New code (server mode - auto-start)**:

.. code-block:: python

   from lynguine.client import ServerClient

   # Client automatically starts server if not running
   client = ServerClient(
       server_url='http://127.0.0.1:8765',
       auto_start=True,           # Enable auto-start
       idle_timeout=300,          # Server shuts down after 5min idle
       max_retries=3,             # Retry on failures
       retry_delay=1.0            # Exponential backoff from 1s
   )

   df = client.read_data(interface_file='config.yml', directory='.')
   client.close()  # Server remains running for other clients

Step 4: Update Your Code Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pattern 1: Single Data Read
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Before**:

.. code-block:: python

   from lynguine.access import io

   df = io.read('config.yml', directory='.')

**After**:

.. code-block:: python

   from lynguine.client import ServerClient

   client = ServerClient(auto_start=True, idle_timeout=300)
   df = client.read_data(interface_file='config.yml', directory='.')
   client.close()

Pattern 2: Multiple Reads (The Big Win!)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Before** (20s for 10 reads):

.. code-block:: python

   from lynguine.access import io

   results = []
   for file in config_files:
       df = io.read(file)  # 2s each
       results.append(df)

**After** (2s + 100ms for 10 reads):

.. code-block:: python

   from lynguine.client import ServerClient

   client = ServerClient(auto_start=True, idle_timeout=300)
   results = []
   for file in config_files:
       df = client.read_data(interface_file=file)  # 10ms each after first
       results.append(df)
   client.close()

Pattern 3: Subprocess Calls (Like ``lamd``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Before**:

.. code-block:: bash

   # Each subprocess incurs full startup cost
   python -c "from lynguine.access import io; io.read(...)"  # 2s
   python -c "from lynguine.access import io; io.read(...)"  # 2s
   python -c "from lynguine.access import io; io.read(...)"  # 2s

**After**:

.. code-block:: bash

   # First call starts server, subsequent calls are fast
   python -c "from lynguine.client import ServerClient; ServerClient(auto_start=True).read_data(...)"  # 2s first time
   python -c "from lynguine.client import ServerClient; ServerClient().read_data(...)"  # 10ms
   python -c "from lynguine.client import ServerClient; ServerClient().read_data(...)"  # 10ms

Pattern 4: Context Manager (Clean Teardown)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from lynguine.client import ServerClient

   with ServerClient(auto_start=True, idle_timeout=300) as client:
       df1 = client.read_data(interface_file='config1.yml')
       df2 = client.read_data(interface_file='config2.yml')
       df3 = client.read_data(interface_file='config3.yml')
   # Client closes automatically, server remains running

Step 5: Configure for Your Use Case
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Development (Persistent Server)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   client = ServerClient(
       auto_start=True,
       idle_timeout=0  # Never auto-shutdown (manual stop only)
   )

For CI/CD (Auto-Cleanup)
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   client = ServerClient(
       auto_start=True,
       idle_timeout=60,  # 1-minute timeout for fast cleanup
       max_retries=2     # Fewer retries for faster failure
   )

For Production (Robust)
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   client = ServerClient(
       auto_start=True,
       idle_timeout=300,    # 5-minute timeout
       max_retries=3,       # Standard retry count
       retry_delay=1.0,     # 1s, 2s, 4s retry delays
       timeout=60.0         # 60s request timeout
   )

Step 6: Test Your Migration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Verify functionality**: Results should be identical to direct mode
2. **Measure performance**: Use benchmarks to confirm speedup
3. **Test failure scenarios**: Kill server, check auto-restart works
4. **Monitor resources**: Check server memory usage over time

.. code-block:: python

   # Benchmark comparison
   import time
   from lynguine.client import ServerClient

   client = ServerClient(auto_start=True)

   # Warmup (first call starts server)
   _ = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})

   # Measure subsequent calls
   start = time.time()
   for _ in range(10):
       _ = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
   elapsed = time.time() - start

   print(f"10 calls: {elapsed:.3f}s ({elapsed/10*1000:.1f}ms per call)")
   # Expected: ~100ms total, ~10ms per call

   client.close()

Application-Specific Integration
---------------------------------

lamd Integration
~~~~~~~~~~~~~~~~

**Before**:

.. code-block:: python

   # lamd calls lynguine via subprocess repeatedly
   subprocess.run(['python', '-c', 'from lynguine.access import io; ...'])

**After**:

.. code-block:: python

   # First call auto-starts server, subsequent calls are fast
   subprocess.run(['python', '-c', '''
   from lynguine.client import ServerClient
   client = ServerClient(auto_start=True, idle_timeout=300)
   client.read_data(...)
   '''])

referia Integration
~~~~~~~~~~~~~~~~~~~

.. warning::
   **Server mode is NOT recommended for referia** because:

   - referia already runs in a long-running Jupyter kernel
   - No repeated subprocess calls = no startup overhead
   - Server mode adds unnecessary complexity

   Continue using direct mode in referia.

Rolling Back
------------

If you need to roll back to direct mode:

.. code-block:: python

   # Before (server mode):
   from lynguine.client import ServerClient
   client = ServerClient()
   df = client.read_data(interface_file='config.yml')

   # After (direct mode):
   from lynguine.access import io
   df = io.read('config.yml')

No data migration needed - both modes work identically!

Performance Expectations
------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 25 25 10

   * - Scenario
     - Direct Mode
     - Server Mode (First)
     - Server Mode (Subsequent)
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
     - **198x**
   * - 100 calls
     - 194.7s
     - 1.947s + 980ms
     - 980ms
     - **~67x**

Next Steps
----------

1. ✅ Migrate your code using auto-start
2. ✅ Measure your actual performance gains
3. ✅ Configure idle timeout for your use case
4. ✅ Add retry logic for production robustness
5. 📚 Read :doc:`troubleshooting` for common issues
6. 📊 Monitor server resources in production

See Also
--------

- :doc:`quickstart` - Quick start guide
- :doc:`api` - Complete API reference
- :doc:`troubleshooting` - Common issues and solutions
- :doc:`examples` - More code examples

