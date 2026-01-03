Quick Start
===========

This guide gets you started with lynguine server mode in under 5 minutes.

Installation
------------

Server mode requires the ``requests`` library:

.. code-block:: bash

   pip install requests

Basic Usage
-----------

Option 1: Auto-Start (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The client automatically starts the server if it's not running:

.. code-block:: python

   from lynguine.client import ServerClient

   # Client handles everything automatically
   client = ServerClient(auto_start=True, idle_timeout=300)
   df = client.read_data(interface_file='config.yml', directory='.')
   client.close()

Option 2: Manual Server Start
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start the server in a separate terminal:

.. code-block:: bash

   # Terminal 1: Start server
   python -m lynguine.server

   # Optional: Custom host/port
   python -m lynguine.server --host 127.0.0.1 --port 8765

   # Optional: With idle timeout (auto-shutdown after 5 minutes)
   python -m lynguine.server --idle-timeout 300

Then use the client:

.. code-block:: python

   # Terminal 2: Use client
   from lynguine.client import ServerClient

   client = ServerClient('http://127.0.0.1:8765')
   df = client.read_data(interface_file='config.yml', directory='.')
   client.close()

Common Patterns
---------------

Single Data Read
~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient

   client = ServerClient(auto_start=True, idle_timeout=300)
   df = client.read_data(interface_file='config.yml', directory='.')
   client.close()

Multiple Reads (The Big Win!)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is where server mode really shines:

.. code-block:: python

   from lynguine.client import ServerClient

   # Before (direct mode): 20s for 10 reads
   # After (server mode): 2s + 100ms for 10 reads

   client = ServerClient(auto_start=True, idle_timeout=300)
   results = []
   
   for file in config_files:
       df = client.read_data(interface_file=file)  # 10ms each after first
       results.append(df)
   
   client.close()

Context Manager
~~~~~~~~~~~~~~~

For automatic cleanup:

.. code-block:: python

   from lynguine.client import ServerClient

   with ServerClient(auto_start=True, idle_timeout=300) as client:
       df1 = client.read_data(interface_file='config1.yml')
       df2 = client.read_data(interface_file='config2.yml')
       df3 = client.read_data(interface_file='config3.yml')
   # Client closes automatically, server remains running

Configuration Options
---------------------

Client Parameters
~~~~~~~~~~~~~~~~~

.. code-block:: python

   client = ServerClient(
       server_url='http://127.0.0.1:8765',  # Server address
       timeout=30.0,                        # Request timeout (seconds)
       auto_start=False,                    # Auto-start server if not running
       idle_timeout=0,                      # Server idle timeout (0=disabled)
       max_retries=3,                       # Retry count on failures
       retry_delay=1.0                      # Base delay for exponential backoff
   )

For Development
~~~~~~~~~~~~~~~

.. code-block:: python

   client = ServerClient(
       auto_start=True,
       idle_timeout=0  # Never auto-shutdown
   )

For CI/CD
~~~~~~~~~

.. code-block:: python

   client = ServerClient(
       auto_start=True,
       idle_timeout=60,   # 1-minute timeout for fast cleanup
       max_retries=2      # Fewer retries for faster failure
   )

For Production
~~~~~~~~~~~~~~

.. code-block:: python

   client = ServerClient(
       auto_start=True,
       idle_timeout=300,    # 5-minute timeout
       max_retries=3,       # Standard retry count
       retry_delay=1.0,     # 1s, 2s, 4s retry delays
       timeout=60.0         # 60s request timeout
   )

Verifying Performance
---------------------

Benchmark your setup to confirm the speedup:

.. code-block:: python

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

Next Steps
----------

- :doc:`migration` - Migrate from direct mode to server mode
- :doc:`api` - Complete API reference
- :doc:`troubleshooting` - Common issues and solutions
- :doc:`examples` - More code examples

