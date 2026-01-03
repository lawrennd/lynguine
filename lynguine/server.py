"""
Lynguine Server Mode - HTTP/REST API for fast repeated access

This module provides a simple HTTP server that keeps lynguine loaded in memory,
avoiding the startup cost (pandas, numpy, etc.) for repeated operations.

This is Phase 1: Proof of Concept - minimal implementation for validation.
"""

import json
import sys
import os
import socket
import signal
import atexit
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any
from pathlib import Path
import traceback

# Import lynguine components
from lynguine.config.interface import Interface
from lynguine.access import io
from lynguine.log import Logger

# Create logger instance
log = Logger(name="lynguine.server", level="info", filename="lynguine-server.log")

# Global reference for cleanup
_lockfile_path = None


def get_lockfile_path(host: str, port: int) -> Path:
    """
    Get the path to the lockfile for a server instance
    
    :param host: Server host address
    :param port: Server port number
    :return: Path to lockfile
    """
    # Use system temp directory for lockfiles
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    
    # Create lockfile name from host and port
    # Replace dots in host with dashes for filename safety
    safe_host = host.replace('.', '-').replace(':', '-')
    lockfile_name = f"lynguine-server-{safe_host}-{port}.lock"
    
    return temp_dir / lockfile_name


def check_server_running(host: str, port: int) -> bool:
    """
    Check if a lynguine server is already running on the specified host:port
    
    This checks both:
    1. If the port is in use (socket check)
    2. If a lynguine server lockfile exists
    
    :param host: Host address to check
    :param port: Port number to check
    :return: True if server is running, False otherwise
    """
    # Method 1: Check if port is in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Attempt to connect
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        if result == 0:
            # Port is in use - likely a server is running
            log.debug(f"Port {port} is in use on {host}")
            return True
    except socket.error:
        pass
    finally:
        sock.close()
    
    # Method 2: Check for lockfile
    lockfile = get_lockfile_path(host, port)
    if lockfile.exists():
        # Lockfile exists - check if process is still alive
        try:
            with open(lockfile, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            try:
                os.kill(pid, 0)  # Signal 0 doesn't kill, just checks existence
                log.debug(f"Lockfile exists for PID {pid} which is still running")
                return True
            except OSError:
                # Process doesn't exist - stale lockfile
                log.warning(f"Stale lockfile found for PID {pid}, cleaning up")
                lockfile.unlink()
                return False
        except (ValueError, IOError):
            # Invalid lockfile
            log.warning(f"Invalid lockfile at {lockfile}, removing")
            try:
                lockfile.unlink()
            except:
                pass
            return False
    
    return False


def create_lockfile(host: str, port: int) -> Path:
    """
    Create a lockfile for this server instance
    
    :param host: Server host address
    :param port: Server port number
    :return: Path to created lockfile
    """
    global _lockfile_path
    
    lockfile = get_lockfile_path(host, port)
    _lockfile_path = lockfile
    
    # Write current process ID to lockfile
    with open(lockfile, 'w') as f:
        f.write(str(os.getpid()))
    
    log.debug(f"Created lockfile at {lockfile}")
    return lockfile


def cleanup_lockfile():
    """Remove the lockfile for this server instance"""
    global _lockfile_path
    
    if _lockfile_path and _lockfile_path.exists():
        try:
            _lockfile_path.unlink()
            log.info(f"Removed lockfile at {_lockfile_path}")
        except Exception as e:
            log.warning(f"Failed to remove lockfile: {e}")
        _lockfile_path = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    cleanup_lockfile()
    sys.exit(0)


class LynguineHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for lynguine server mode.
    
    Handles POST requests to /api endpoints for various lynguine operations.
    """
    
    def log_message(self, format, *args):
        """Override to use lynguine logging"""
        log.info(f"Server: {format % args}")
    
    def send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send a JSON response with appropriate headers"""
        response_json = json.dumps(data)
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_json)))
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, error: Exception, status_code: int = 500):
        """Send an error response"""
        error_data = {
            'status': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        self.send_json_response(error_data, status_code)
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error_response(ValueError("Empty request body"), 400)
                return
            
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))
            
            # Route to appropriate handler
            if self.path == '/api/read_data':
                self.handle_read_data(request_data)
            elif self.path == '/api/health':
                self.handle_health()
            elif self.path == '/api/ping':
                self.handle_ping()
            else:
                self.send_error_response(
                    ValueError(f"Unknown endpoint: {self.path}"), 
                    404
                )
        except json.JSONDecodeError as e:
            self.send_error_response(e, 400)
        except Exception as e:
            log.error(f"Error handling request: {e}")
            self.send_error_response(e, 500)
    
    def do_GET(self):
        """Handle GET requests (health check, ping)"""
        if self.path == '/api/health':
            self.handle_health()
        elif self.path == '/api/ping':
            self.handle_ping()
        else:
            self.send_error_response(
                ValueError(f"GET not supported for: {self.path}"), 
                405
            )
    
    def handle_ping(self):
        """Simple ping endpoint for connectivity testing"""
        self.send_json_response({
            'status': 'ok',
            'message': 'pong'
        })
    
    def handle_health(self):
        """Health check endpoint"""
        self.send_json_response({
            'status': 'ok',
            'server': 'lynguine-server-poc',
            'version': '0.1.0'
        })
    
    def handle_read_data(self, request_data: Dict[str, Any]):
        """
        Handle read_data operation
        
        Expected request format:
        {
            "interface_file": "path/to/config.yml",
            "interface_field": "optional_field",  # optional
            "directory": ".",  # optional, defaults to current directory
        }
        OR
        {
            "data_source": {
                "type": "csv",
                "filename": "data.csv",
                ...
            }
        }
        """
        try:
            # Option 1: Load from interface file
            if 'interface_file' in request_data:
                interface_file = request_data['interface_file']
                directory = request_data.get('directory', '.')
                field = request_data.get('interface_field', None)
                
                log.debug(f"Loading interface from {interface_file} in {directory}")
                interface = Interface.from_file(
                    user_file=interface_file,
                    directory=directory,
                    field=field
                )
                
                # Read data from the interface's input configuration
                if 'input' not in interface._data:
                    raise ValueError("Interface has no 'input' section")
                
                input_config = interface._data['input']
                result = io.read_data(input_config)
                # read_data returns (DataFrame, Interface) tuple
                if isinstance(result, tuple):
                    df, _ = result
                else:
                    df = result
                
            # Option 2: Direct data source specification
            elif 'data_source' in request_data:
                data_source = request_data['data_source']
                log.debug(f"Reading data from source: {data_source.get('type', 'unknown')}")
                result = io.read_data(data_source)
                # read_data returns (DataFrame, Interface) tuple
                if isinstance(result, tuple):
                    df, _ = result
                else:
                    df = result
            
            else:
                raise ValueError(
                    "Request must include either 'interface_file' or 'data_source'"
                )
            
            # Convert DataFrame to dict for JSON serialization
            # Note: This is simplified for PoC. Full implementation would support
            # multiple serialization formats and handle large datasets differently.
            result = {
                'status': 'success',
                'data': {
                    'records': df.to_dict('records'),
                    'columns': list(df.columns),
                    'shape': df.shape,
                    'dtypes': {k: str(v) for k, v in df.dtypes.items()}
                }
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            log.error(f"Error in handle_read_data: {e}")
            self.send_error_response(e)


def run_server(host: str = '127.0.0.1', port: int = 8765):
    """
    Start the lynguine HTTP server
    
    Checks if a server is already running on the specified host:port
    and prevents duplicate instances.
    
    :param host: Host address to bind to (default: 127.0.0.1 for localhost only)
    :param port: Port number to listen on (default: 8765)
    :raises RuntimeError: If server is already running on this host:port
    """
    # Check if server is already running
    if check_server_running(host, port):
        error_msg = (
            f"A lynguine server is already running on http://{host}:{port}\n"
            f"To connect to the existing server:\n"
            f"  from lynguine.client import ServerClient\n"
            f"  client = ServerClient('http://{host}:{port}')\n"
            f"\n"
            f"To start a new server on a different port:\n"
            f"  python -m lynguine.server --port {port + 1}"
        )
        print(f"ERROR: {error_msg}")
        raise RuntimeError(error_msg)
    
    # Create lockfile
    create_lockfile(host, port)
    
    # Register cleanup handlers
    atexit.register(cleanup_lockfile)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, LynguineHandler)
    
    print(f"Lynguine Server Mode (PoC)")
    print(f"==========================")
    print(f"Server starting on http://{host}:{port}")
    print(f"PID: {os.getpid()}")
    print(f"Press Ctrl+C to stop")
    print()
    print(f"Available endpoints:")
    print(f"  GET  /api/health     - Health check")
    print(f"  GET  /api/ping       - Connectivity test")
    print(f"  POST /api/read_data  - Read data via lynguine")
    print()
    
    log.info(f"Server started on {host}:{port} (PID: {os.getpid()})")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
        cleanup_lockfile()
        log.info("Server stopped")
        print("Server stopped.")


if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Lynguine Server Mode (PoC)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8765, help='Port to listen on (default: 8765)')
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port)

