API Reference
=============

This page provides complete API documentation for lynguine server mode.

Client API
----------

ServerClient
~~~~~~~~~~~~

.. autoclass:: lynguine.client.ServerClient
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __enter__, __exit__

   **Parameters:**

   :param server_url: URL of the lynguine server (default: ``'http://127.0.0.1:8765'``)
   :type server_url: str
   :param timeout: Request timeout in seconds (default: ``30.0``)
   :type timeout: float
   :param auto_start: Auto-start server if not running (default: ``False``)
   :type auto_start: bool
   :param idle_timeout: Server idle timeout in seconds when auto-starting (default: ``0`` = disabled)
   :type idle_timeout: int
   :param max_retries: Maximum number of retries for failed requests (default: ``3``)
   :type max_retries: int
   :param retry_delay: Base delay between retries in seconds, uses exponential backoff (default: ``1.0``)
   :type retry_delay: float

   **Example:**

   .. code-block:: python

      from lynguine.client import ServerClient

      # Basic usage
      client = ServerClient()
      df = client.read_data(interface_file='config.yml')
      client.close()

      # With auto-start and retry logic
      client = ServerClient(
          auto_start=True,
          idle_timeout=300,
          max_retries=3,
          retry_delay=1.0
      )

      # As context manager
      with ServerClient(auto_start=True) as client:
          df = client.read_data(interface_file='config.yml')

Methods
^^^^^^^

ping()
""""""

Test connectivity to the server.

:returns: ``True`` if server is reachable, ``False`` otherwise
:rtype: bool

.. code-block:: python

   if client.ping():
       print("Server is online")

health_check()
""""""""""""""

Get server health status with automatic retry on failure.

:returns: Server health information dictionary
:rtype: Dict[str, Any]
:raises RuntimeError: If server is not available after retries
:raises requests.HTTPError: If request fails

.. code-block:: python

   health = client.health_check()
   print(health['status'])  # 'ok'

read_data()
"""""""""""

Read data via the lynguine server with automatic retry on failure.

:param interface_file: Path to lynguine interface YAML file
:type interface_file: Optional[str]
:param directory: Directory for resolving relative paths (default: ``'.'``)
:type directory: str
:param interface_field: Optional field name within interface
:type interface_field: Optional[str]
:param data_source: Direct data source specification (dict with 'type', 'filename', etc.)
:type data_source: Optional[Dict[str, Any]]
:returns: DataFrame containing the data
:rtype: pd.DataFrame
:raises ValueError: If neither interface_file nor data_source is provided
:raises RuntimeError: If server is not available after retries
:raises requests.HTTPError: If request fails

.. code-block:: python

   # Using interface file
   df = client.read_data(
       interface_file='config.yml',
       directory='.'
   )

   # Using direct data source
   df = client.read_data(
       data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']}
   )

close()
"""""""

Close the client session.

.. note::
   Does NOT stop auto-started servers by design. Auto-started servers remain 
   running for other clients and will shut down via idle timeout if configured.

.. code-block:: python

   client.close()

Convenience Function
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lynguine.client.create_client

   **Example:**

   .. code-block:: python

      from lynguine.client import create_client

      client = create_client('http://127.0.0.1:8765')

Server API
----------

Starting the Server
~~~~~~~~~~~~~~~~~~~

Command Line
""""""""""""

.. code-block:: bash

   # Basic usage
   python -m lynguine.server

   # Custom host and port
   python -m lynguine.server --host 127.0.0.1 --port 8765

   # With idle timeout (auto-shutdown after inactivity)
   python -m lynguine.server --idle-timeout 300  # 5 minutes

Programmatic
""""""""""""

.. autofunction:: lynguine.server.run_server

   **Parameters:**

   :param host: Host address to bind to (default: ``'127.0.0.1'`` for localhost only)
   :type host: str
   :param port: Port number to listen on (default: ``8765``)
   :type port: int
   :param idle_timeout: Seconds of inactivity before auto-shutdown (default: ``0`` = disabled)
   :type idle_timeout: int
   :raises RuntimeError: If port is already in use

   **Example:**

   .. code-block:: python

      from lynguine.server import run_server

      # Start server programmatically
      run_server(host='127.0.0.1', port=8765, idle_timeout=300)

Server Endpoints
~~~~~~~~~~~~~~~~

The server provides the following HTTP/REST API endpoints:

Health Check
""""""""""""

**GET** ``/api/health``

Returns server health status.

**Response:**

.. code-block:: json

   {
     "status": "ok"
   }

Ping
""""

**GET** ``/api/ping``

Tests server connectivity.

**Response:**

.. code-block:: json

   {
     "message": "pong"
   }

Status
""""""

**GET** or **POST** ``/api/status``

Returns detailed server diagnostics.

**Response:**

.. code-block:: json

   {
     "status": "ok",
     "server": "lynguine-server",
     "version": "0.2.0",
     "pid": 12345,
     "uptime_seconds": 125.3,
     "memory": {
       "rss_mb": 117.5,
       "percent": 1.2
     },
     "cpu_percent": 0.5,
     "idle_timeout": {
       "enabled": true,
       "timeout_seconds": 300,
       "idle_seconds": 45.2,
       "remaining_seconds": 254.8
     },
     "endpoints": [
       "GET  /api/health",
       "GET  /api/ping",
       "GET  /api/status",
       "POST /api/read_data",
       "POST /api/write_data",
       "POST /api/compute"
     ]
   }

Read Data
"""""""""

**POST** ``/api/read_data``

Reads data via lynguine.

**Request:**

.. code-block:: json

   {
     "interface_file": "config.yml",
     "directory": ".",
     "interface_field": null,
     "data_source": null
   }

Or with direct data source:

.. code-block:: json

   {
     "data_source": {
       "type": "fake",
       "nrows": 10,
       "cols": ["name", "email"]
     }
   }

**Response:**

.. code-block:: json

   {
     "status": "success",
     "data": {
       "records": [...],
       "shape": [10, 2]
     }
   }

Write Data
""""""""""

**POST** ``/api/write_data``

Writes data via lynguine.

**Request:**

.. code-block:: json

   {
     "data": {
       "records": [...],
       "columns": ["name", "age"]
     },
     "output": {
       "type": "csv",
       "filename": "output.csv"
     }
   }

**Response:**

.. code-block:: json

   {
     "status": "success",
     "message": "Wrote 10 records to output.csv"
   }

Compute
"""""""

**POST** ``/api/compute``

Runs compute operations (placeholder for compute framework integration).

**Request:**

.. code-block:: json

   {
     "operation": "test_compute",
     "data": {
       "records": [...]
     },
     "params": {
       "param1": "value1"
     }
   }

**Response:**

.. code-block:: json

   {
     "status": "success",
     "operation": "test_compute",
     "message": "Compute operation completed"
   }

Utility Functions
-----------------

.. autofunction:: lynguine.server.check_server_running

   **Parameters:**

   :param host: Server host address
   :type host: str
   :param port: Server port number
   :type port: int
   :returns: Tuple of (is_running: bool, server_type: str)
   :rtype: tuple[bool, str]

   **Example:**

   .. code-block:: python

      from lynguine.server import check_server_running

      is_running, server_type = check_server_running('127.0.0.1', 8765)
      if is_running:
          if server_type == 'lynguine':
              print("Lynguine server is running")
          else:
              print("Another application is using the port")

Error Handling
--------------

The client automatically handles the following errors with retry logic:

Connection Errors
~~~~~~~~~~~~~~~~~

- ``requests.ConnectionError``: Server not reachable
- ``requests.Timeout``: Request timed out
- **Behavior**: Retry with exponential backoff

Server Errors (5xx)
~~~~~~~~~~~~~~~~~~~

- HTTP 500-599 status codes
- **Behavior**: Retry with exponential backoff

Client Errors (4xx)
~~~~~~~~~~~~~~~~~~~

- HTTP 400-499 status codes (e.g., bad request, not found)
- **Behavior**: Immediate failure, no retry

Example with error handling:

.. code-block:: python

   from lynguine.client import ServerClient
   import requests

   client = ServerClient(auto_start=True, max_retries=3)

   try:
       df = client.read_data(interface_file='config.yml')
   except requests.HTTPError as e:
       # 4xx error - bad request
       print(f"Client error: {e.response.status_code}")
   except RuntimeError as e:
       # Server not available after retries
       print(f"Server unavailable: {e}")
   finally:
       client.close()

Performance Considerations
--------------------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

The client uses ``requests.Session()`` for connection pooling, which reuses TCP connections for better performance.

Timeout Configuration
~~~~~~~~~~~~~~~~~~~~~

The ``timeout`` parameter controls how long to wait for a response:

- **Too short**: May cause premature timeouts on slow operations
- **Too long**: May delay error detection
- **Recommended**: 30-60 seconds for most use cases

Retry Strategy
~~~~~~~~~~~~~~

Exponential backoff with base delay:

- Attempt 1: Immediate
- Attempt 2: ``retry_delay * 2^0`` = 1s (default)
- Attempt 3: ``retry_delay * 2^1`` = 2s
- Attempt 4: ``retry_delay * 2^2`` = 4s

Total delay for 3 retries with 1s base: ~7s

See Also
--------

- :doc:`quickstart` - Quick start guide
- :doc:`migration` - Migration from direct mode
- :doc:`troubleshooting` - Common issues and solutions
- :doc:`examples` - Code examples

