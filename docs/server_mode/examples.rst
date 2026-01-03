Examples
========

This page provides code examples for common server mode use cases.

Basic Examples
--------------

Simple Client Usage
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient

   # Create client with auto-start
   client = ServerClient(auto_start=True, idle_timeout=300)

   # Read data
   df = client.read_data(interface_file='config.yml', directory='.')

   # Close client
   client.close()

Context Manager
~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient

   with ServerClient(auto_start=True, idle_timeout=300) as client:
       df1 = client.read_data(interface_file='config1.yml')
       df2 = client.read_data(interface_file='config2.yml')
       df3 = client.read_data(interface_file='config3.yml')
   # Automatic cleanup

Batch Processing
----------------

Processing Multiple Files
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient
   from pathlib import Path

   config_files = list(Path('configs/').glob('*.yml'))

   with ServerClient(auto_start=True, idle_timeout=300) as client:
       results = []
       for config_file in config_files:
           df = client.read_data(interface_file=str(config_file))
           results.append(df)

   # Process results
   for i, df in enumerate(results):
       print(f"File {i}: {len(df)} rows")

Data Pipeline
~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient
   import pandas as pd

   def process_pipeline(input_files, output_file):
       """Process multiple files and combine results"""
       with ServerClient(auto_start=True, idle_timeout=300) as client:
           # Read all files
           dfs = []
           for file in input_files:
               df = client.read_data(interface_file=file)
               dfs.append(df)

           # Combine and process
           combined = pd.concat(dfs, ignore_index=True)

           # Save result
           combined.to_csv(output_file, index=False)
           print(f"Processed {len(dfs)} files, {len(combined)} total rows")

   # Usage
   process_pipeline(['file1.yml', 'file2.yml', 'file3.yml'], 'output.csv')

Production Patterns
-------------------

Robust Client with Retry Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient
   import logging

   # Configure logging
   logging.basicConfig(level=logging.INFO)

   def create_production_client():
       """Create a production-ready client"""
       return ServerClient(
           server_url='http://127.0.0.1:8765',
           auto_start=True,
           idle_timeout=300,      # 5-minute timeout
           max_retries=3,         # Retry up to 3 times
           retry_delay=1.0,       # Start with 1s delay
           timeout=60.0           # 60s request timeout
       )

   # Usage
   with create_production_client() as client:
       try:
           df = client.read_data(interface_file='config.yml')
           print(f"Successfully read {len(df)} rows")
       except Exception as e:
           logging.error(f"Failed to read data: {e}")
           raise

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient
   import requests

   client = ServerClient(auto_start=True, max_retries=3)

   try:
       df = client.read_data(interface_file='config.yml')
   except requests.HTTPError as e:
       if e.response.status_code == 404:
           print("Config file not found")
       elif e.response.status_code == 400:
           print("Invalid request")
       else:
           print(f"Server error: {e.response.status_code}")
   except RuntimeError as e:
       print(f"Server unavailable after retries: {e}")
   except ValueError as e:
       print(f"Invalid configuration: {e}")
   finally:
       client.close()

Configuration-Specific Examples
-------------------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient

   # Development: persistent server, no timeout
   client = ServerClient(
       auto_start=True,
       idle_timeout=0,  # Never auto-shutdown
       max_retries=1    # Fail fast in development
   )

CI/CD Environment
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient

   # CI/CD: fast cleanup, fewer retries
   client = ServerClient(
       auto_start=True,
       idle_timeout=60,   # 1-minute timeout
       max_retries=2,     # Fewer retries
       retry_delay=0.5    # Faster retries
   )

Production Environment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient

   # Production: robust with retries
   client = ServerClient(
       auto_start=True,
       idle_timeout=300,    # 5-minute timeout
       max_retries=3,       # Standard retries
       retry_delay=1.0,     # Exponential backoff
       timeout=60.0         # 60s request timeout
   )

Performance Benchmarking
------------------------

Simple Benchmark
~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   from lynguine.client import ServerClient

   def benchmark_server_mode(num_calls=10):
       """Benchmark server mode performance"""
       client = ServerClient(auto_start=True)

       # Warmup
       _ = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})

       # Measure
       start = time.time()
       for _ in range(num_calls):
           _ = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
       elapsed = time.time() - start

       print(f"{num_calls} calls: {elapsed:.3f}s ({elapsed/num_calls*1000:.1f}ms per call)")
       client.close()

   benchmark_server_mode(10)

Comparison Benchmark
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   from lynguine.access import io
   from lynguine.client import ServerClient

   def benchmark_comparison(num_calls=10):
       """Compare direct mode vs server mode"""

       # Direct mode
       print("Direct mode:")
       start = time.time()
       for _ in range(num_calls):
           _ = io.read_fake(nrows=10, cols=['name'])
       direct_time = time.time() - start
       print(f"  {num_calls} calls: {direct_time:.3f}s")

       # Server mode
       print("Server mode:")
       client = ServerClient(auto_start=True)

       # Warmup
       _ = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})

       # Measure
       start = time.time()
       for _ in range(num_calls):
           _ = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
       server_time = time.time() - start
       print(f"  {num_calls} calls: {server_time:.3f}s")

       client.close()

       # Report
       speedup = direct_time / server_time
       print(f"\nSpeedup: {speedup:.1f}x")

   benchmark_comparison(10)

Advanced Usage
--------------

Custom Data Source
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient

   # Define custom data source
   data_source = {
       'type': 'fake',
       'nrows': 100,
       'cols': ['name', 'email', 'age']
   }

   with ServerClient(auto_start=True) as client:
       df = client.read_data(data_source=data_source)
       print(df.head())

Multiple Concurrent Clients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient
   import concurrent.futures

   def process_file(file):
       """Process a single file"""
       with ServerClient() as client:  # Connects to existing server
           df = client.read_data(interface_file=file)
           return len(df)

   # Process files in parallel
   files = ['file1.yml', 'file2.yml', 'file3.yml']

   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
       results = list(executor.map(process_file, files))

   print(f"Processed {sum(results)} total rows")

Monitoring Server Health
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.client import ServerClient
   import time

   def monitor_server(duration=60, interval=10):
       """Monitor server health for specified duration"""
       client = ServerClient()

       end_time = time.time() + duration
       while time.time() < end_time:
           try:
               if client.ping():
                   health = client.health_check()
                   print(f"Server OK: {health}")
               else:
                   print("Server not responding")
           except Exception as e:
               print(f"Error: {e}")

           time.sleep(interval)

       client.close()

   monitor_server(duration=60, interval=10)

Integration Examples
--------------------

Flask Integration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flask import Flask, jsonify, request
   from lynguine.client import ServerClient

   app = Flask(__name__)

   # Create a single client instance
   client = ServerClient(auto_start=True, idle_timeout=300)

   @app.route('/data/<config_file>')
   def get_data(config_file):
       """Read data via lynguine server"""
       try:
           df = client.read_data(interface_file=f'configs/{config_file}.yml')
           return jsonify({
               'rows': len(df),
               'columns': list(df.columns),
               'data': df.to_dict('records')[:10]  # First 10 rows
           })
       except Exception as e:
           return jsonify({'error': str(e)}), 500

   if __name__ == '__main__':
       app.run()

Command-Line Tool
~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python
   """Simple CLI tool using lynguine server mode"""
   import argparse
   from lynguine.client import ServerClient

   def main():
       parser = argparse.ArgumentParser(description='Read data via lynguine')
       parser.add_argument('config', help='Config file to read')
       parser.add_argument('--output', help='Output CSV file')
       args = parser.parse_args()

       with ServerClient(auto_start=True, idle_timeout=300) as client:
           df = client.read_data(interface_file=args.config)
           print(f"Read {len(df)} rows, {len(df.columns)} columns")

           if args.output:
               df.to_csv(args.output, index=False)
               print(f"Saved to {args.output}")
           else:
               print(df.head())

   if __name__ == '__main__':
       main()

Testing Examples
----------------

Unit Test with Mock
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import unittest
   from unittest.mock import patch, MagicMock
   from lynguine.client import ServerClient

   class TestServerClient(unittest.TestCase):
       @patch('lynguine.client.requests.Session')
       def test_read_data(self, mock_session):
           """Test read_data with mocked server"""
           # Setup mock
           mock_response = MagicMock()
           mock_response.status_code = 200
           mock_response.json.return_value = {
               'status': 'success',
               'data': {
                   'records': [{'name': 'Alice'}, {'name': 'Bob'}],
                   'shape': [2, 1]
               }
           }
           mock_session.return_value.post.return_value = mock_response

           # Test
           client = ServerClient()
           df = client.read_data(data_source={'type': 'fake', 'nrows': 2})

           self.assertEqual(len(df), 2)
           client.close()

Integration Test
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from lynguine.client import ServerClient

   def test_server_integration():
       """Integration test with real server"""
       client = ServerClient(auto_start=True, idle_timeout=60)

       try:
           # Test ping
           assert client.ping() is True

           # Test health check
           health = client.health_check()
           assert health['status'] == 'ok'

           # Test read_data
           df = client.read_data(data_source={'type': 'fake', 'nrows': 10, 'cols': ['name']})
           assert len(df) == 10
           assert 'name' in df.columns

       finally:
           client.close()

See Also
--------

- :doc:`quickstart` - Quick start guide
- :doc:`migration` - Migration from direct mode
- :doc:`api` - Complete API reference
- :doc:`troubleshooting` - Common issues and solutions

