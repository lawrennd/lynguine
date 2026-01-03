Troubleshooting
===============

This guide helps you diagnose and fix common issues with lynguine server mode.

Quick Fixes
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Problem
     - Quick Fix
   * - Port in use
     - ``python -m lynguine.server --port 8766``
   * - Server not starting
     - ``rm /tmp/lynguine-server-* && python -m lynguine.server``
   * - Connection refused
     - ``client = ServerClient(auto_start=True)``
   * - Slow first call
     - Expected - subsequent calls are fast
   * - Memory growing
     - ``python -m lynguine.server --idle-timeout 600``
   * - Auto-start failing
     - Check ``which python`` and environment
   * - Retries not working
     - ``client = ServerClient(max_retries=3)``

Server Won't Start
------------------

Port Already in Use
~~~~~~~~~~~~~~~~~~~

**Symptom:**

.. code-block:: bash

   $ python -m lynguine.server
   ERROR: Port 8765 is already in use...

**Diagnosis:**

.. code-block:: bash

   # macOS/Linux: Find what's using the port
   lsof -i :8765

   # Or use netstat
   netstat -an | grep 8765

**Solutions:**

1. **Use a different port:**

   .. code-block:: bash

      python -m lynguine.server --port 8766

   .. code-block:: python

      client = ServerClient('http://127.0.0.1:8766')

2. **Stop the other application:**

   .. code-block:: bash

      kill <PID>  # Use PID from lsof output

3. **Stop existing lynguine server:**

   .. code-block:: bash

      # Find PID from lockfile
      cat /tmp/lynguine-server-127-0-0-1-8765.lock
      kill <PID>

Permission Denied
~~~~~~~~~~~~~~~~~

**Symptom:**

.. code-block:: text

   PermissionError: [Errno 13] Permission denied

**Solution:**

Don't use privileged ports (< 1024):

.. code-block:: bash

   # Good
   python -m lynguine.server --port 8765

   # Bad (requires root)
   python -m lynguine.server --port 80

Connection Refused Errors
-------------------------

**Symptom:**

.. code-block:: python

   requests.exceptions.ConnectionError: Connection refused

**Causes & Solutions:**

Server Not Running
~~~~~~~~~~~~~~~~~~

**Check:**

.. code-block:: bash

   curl http://127.0.0.1:8765/api/health

**Solutions:**

.. code-block:: python

   # Option A: Start server manually
   # Terminal 1: python -m lynguine.server

   # Option B: Use auto-start (recommended)
   client = ServerClient(auto_start=True)

Wrong URL or Port
~~~~~~~~~~~~~~~~~

**Check configuration:**

.. code-block:: python

   # Wrong
   client = ServerClient('http://127.0.0.1:8764')

   # Correct
   client = ServerClient('http://127.0.0.1:8765')

Server Crashes or Stops Unexpectedly
-------------------------------------

Idle Timeout Triggered
~~~~~~~~~~~~~~~~~~~~~~

**Check if idle timeout is configured:**

.. code-block:: bash

   # Server shows this on startup if enabled:
   # Idle timeout: 300s (5.0 minutes)

**Solutions:**

.. code-block:: bash

   # Option A: Disable idle timeout
   python -m lynguine.server --idle-timeout 0

   # Option B: Increase idle timeout
   python -m lynguine.server --idle-timeout 3600  # 1 hour

   # Option C: Use auto-start (recommended)
   client = ServerClient(auto_start=True, idle_timeout=300)

Out of Memory
~~~~~~~~~~~~~

**Check memory usage:**

.. code-block:: bash

   ps aux | grep lynguine.server

**Solutions:**

.. code-block:: bash

   # Use idle timeout to prevent memory buildup
   python -m lynguine.server --idle-timeout 600

Uncaught Exception
~~~~~~~~~~~~~~~~~~

**Check server logs:**

.. code-block:: bash

   tail -f lynguine-server.log

**Solution:**

Use retry logic to auto-restart:

.. code-block:: python

   client = ServerClient(
       auto_start=True,
       max_retries=3,
       retry_delay=1.0
   )

Slow Performance
----------------

First Call is Always Slow
~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   **This is expected behavior**:
   
   - First call: ~2s (server startup)
   - Subsequent calls: ~10ms

**Verify performance:**

.. code-block:: python

   import time
   from lynguine.client import ServerClient

   client = ServerClient(auto_start=True)

   # First call (slow)
   start = time.time()
   df1 = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
   print(f"First call: {time.time() - start:.3f}s")  # ~2s

   # Subsequent calls (fast)
   start = time.time()
   df2 = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
   print(f"Second call: {time.time() - start:.3f}s")  # ~0.01s

   client.close()

Network Overhead
~~~~~~~~~~~~~~~~

**If using remote server:**

.. code-block:: bash

   # Check network latency
   curl -w "@curl-format.txt" -o /dev/null -s http://server:8765/api/health

**Solution:**

Use localhost for best performance:

.. code-block:: python

   # Best performance
   client = ServerClient('http://127.0.0.1:8765')

   # Slower (network latency)
   client = ServerClient('http://remote-server:8765')

Memory Issues
-------------

**Monitor server memory:**

.. code-block:: bash

   ps aux | grep lynguine.server

**Solutions:**

1. **Use idle timeout:**

   .. code-block:: bash

      python -m lynguine.server --idle-timeout 600  # 10 minutes

2. **Monitor and alert:**

   .. code-block:: python

      response = requests.get('http://127.0.0.1:8765/api/status')
      memory_mb = response.json()['memory']['rss_mb']

      if memory_mb > 1000:  # 1GB threshold
          # Alert or restart
          pass

Auto-Start Not Working
----------------------

Python Not in PATH
~~~~~~~~~~~~~~~~~~

**Check:**

.. code-block:: bash

   which python
   python --version

**Solution:**

Ensure python is in PATH:

.. code-block:: bash

   export PATH="/usr/local/bin:$PATH"

Wrong Python Environment
~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Client starts server in different environment

**Solution:**

Ensure same environment for both:

.. code-block:: bash

   source venv/bin/activate
   python your_script.py

Port Already in Use
~~~~~~~~~~~~~~~~~~~

**Check:**

.. code-block:: bash

   lsof -i :8765

**Solution:**

Use different port:

.. code-block:: python

   client = ServerClient(
       server_url='http://127.0.0.1:8766',
       auto_start=True
   )

Retry Logic Not Working
-----------------------

max_retries=0
~~~~~~~~~~~~~

**Check configuration:**

.. code-block:: python

   client = ServerClient(max_retries=0)  # No retries!

**Solution:**

.. code-block:: python

   client = ServerClient(max_retries=3)  # Enable retries

4xx Errors Don't Retry
~~~~~~~~~~~~~~~~~~~~~~

.. note::
   **This is intentional** - client errors (4xx) indicate invalid requests and should not be retried.

**Example:**

.. code-block:: python

   # This will NOT retry (400 Bad Request)
   client.read_data()  # Missing required params

   # This WILL retry (server crash = connection error)
   # (Server crashes mid-request)

Enable Retry Logging
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.DEBUG)

   # You'll see:
   # WARNING lynguine.client read_data failed (attempt 1/4): 
   #         Connection refused. Retrying in 1.0s...

General Debugging Tips
----------------------

Enable Debug Logging
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging

   # All logs
   logging.basicConfig(level=logging.DEBUG)

   # Or just lynguine logs
   logging.getLogger('lynguine').setLevel(logging.DEBUG)

Check Server Logs
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Server logs to lynguine-server.log
   tail -f lynguine-server.log

   # Or run server in foreground
   python -m lynguine.server

Test Server Manually
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Health check
   curl http://127.0.0.1:8765/api/health

   # Ping
   curl http://127.0.0.1:8765/api/ping

   # Status (detailed)
   curl http://127.0.0.1:8765/api/status | python -m json.tool

Verify Versions
~~~~~~~~~~~~~~~

.. code-block:: python

   import lynguine
   import requests
   import pandas

   print(f"Lynguine: {lynguine.__version__}")
   print(f"Requests: {requests.__version__}")
   print(f"Pandas: {pandas.__version__}")

Run Tests
~~~~~~~~~

.. code-block:: bash

   # Verify installation
   pytest lynguine/tests/test_server_mode.py -v

   # Run specific test class
   pytest lynguine/tests/test_server_mode.py::TestRetryLogic -v

Monitor Server Status
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import requests

   response = requests.get('http://127.0.0.1:8765/api/status')
   status = response.json()

   print(f"Server: {status['server']} v{status['version']}")
   print(f"PID: {status['pid']}")
   print(f"Uptime: {status['uptime_seconds']:.0f}s")
   print(f"Memory: {status['memory']['rss_mb']:.1f}MB")
   print(f"CPU: {status['cpu_percent']:.1f}%")

   if status['idle_timeout']['enabled']:
       remaining = status['idle_timeout']['remaining_seconds']
       print(f"Idle timeout: {remaining:.0f}s remaining")

Common Commands Reference
-------------------------

.. code-block:: bash

   # Start server
   python -m lynguine.server

   # Start with options
   python -m lynguine.server --port 8766 --idle-timeout 300

   # Check if server is running
   curl http://127.0.0.1:8765/api/health

   # Find what's using a port
   lsof -i :8765

   # Kill server by PID
   kill <PID>

   # Clean up lockfiles
   rm /tmp/lynguine-server-*

   # Run tests
   pytest lynguine/tests/test_server_mode.py -v

   # Watch server logs
   tail -f lynguine-server.log

Still Having Issues?
--------------------

1. Check the :doc:`migration` guide
2. Review the :doc:`quickstart`
3. Check the :doc:`api` documentation
4. Run the tests: ``pytest lynguine/tests/test_server_mode.py -v``
5. Check `GitHub issues <https://github.com/lawrennd/lynguine/issues>`_
6. File a bug report with logs, config, and steps to reproduce

See Also
--------

- :doc:`quickstart` - Quick start guide
- :doc:`migration` - Migration from direct mode
- :doc:`api` - Complete API reference
- :doc:`examples` - Code examples

