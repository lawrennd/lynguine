"""
Lynguine Server Mode - HTTP/REST API for fast repeated access

This module provides a simple HTTP server that keeps lynguine loaded in memory,
avoiding the startup cost (pandas, numpy, etc.) for repeated operations.

Phase 1: Proof of Concept - basic functionality validated
Phase 2: Core Features - production-ready single-user server
"""

import json
import sys
import os
import socket
import signal
import atexit
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
from pathlib import Path
import traceback

# Import lynguine components
from lynguine.config.interface import Interface
from lynguine.access import io
from lynguine.log import Logger
from lynguine.session_manager import SessionManager
from lynguine import server_session_handlers

# Create logger instance
log = Logger(name="lynguine.server", level="info", filename="lynguine-server.log")

# Global reference for cleanup
_lockfile_path = None

# Global idle timeout manager
_idle_timeout_manager: Optional['IdleTimeoutManager'] = None

# Global session manager (Phase 5)
_session_manager: Optional[SessionManager] = None


class IdleTimeoutManager:
    """
    Manages idle timeout for server auto-shutdown
    
    Monitors server activity and triggers graceful shutdown
    after a period of inactivity.
    """
    
    def __init__(self, timeout_seconds: int, shutdown_callback):
        """
        Initialize idle timeout manager
        
        :param timeout_seconds: Seconds of inactivity before shutdown (0 = disabled)
        :param shutdown_callback: Function to call for shutdown
        """
        self.timeout_seconds = timeout_seconds
        self.shutdown_callback = shutdown_callback
        self.last_activity = time.time()
        self._monitor_thread = None
        self._shutdown_triggered = False
        self._lock = threading.Lock()
        
        if timeout_seconds > 0:
            self.start()
    
    def start(self):
        """Start the idle timeout monitoring thread"""
        if self.timeout_seconds <= 0:
            return
        
        self._monitor_thread = threading.Thread(
            target=self._monitor_idle,
            daemon=True,
            name="IdleTimeoutMonitor"
        )
        self._monitor_thread.start()
        log.info(f"Idle timeout enabled: {self.timeout_seconds}s ({self.timeout_seconds/60:.1f} minutes)")
    
    def update_activity(self):
        """Update the last activity timestamp"""
        with self._lock:
            self.last_activity = time.time()
    
    def get_idle_time(self) -> float:
        """Get current idle time in seconds"""
        with self._lock:
            return time.time() - self.last_activity
    
    def _monitor_idle(self):
        """Background thread that monitors idle time"""
        # Use adaptive check interval: check every 10s or timeout/4, whichever is smaller
        # This ensures responsive shutdown for short timeouts
        check_interval = min(10, max(1, self.timeout_seconds / 4))
        
        while not self._shutdown_triggered:
            time.sleep(check_interval)
            
            idle_time = self.get_idle_time()
            
            if idle_time >= self.timeout_seconds:
                log.info(f"Idle timeout reached ({idle_time:.1f}s), shutting down server")
                with self._lock:
                    self._shutdown_triggered = True
                
                # Trigger shutdown
                self.shutdown_callback()
                break
    
    def stop(self):
        """Stop the idle timeout monitoring"""
        self._shutdown_triggered = True
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)


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


def check_server_running(host: str, port: int) -> tuple[bool, str]:
    """
    Check if a lynguine server is already running on the specified host:port
    
    This checks both:
    1. If the port is in use (socket check)
    2. If a lynguine server lockfile exists
    
    :param host: Host address to check
    :param port: Port number to check
    :return: Tuple of (is_running: bool, type: str) where type is 'lynguine', 'other', or 'none'
    """
    port_in_use = False
    
    # Method 1: Check if port is in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Attempt to connect
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        if result == 0:
            # Port is in use
            port_in_use = True
            log.debug(f"Port {port} is in use on {host}")
    except socket.error:
        pass
    finally:
        sock.close()
    
    # Method 2: Check for lockfile
    lockfile = get_lockfile_path(host, port)
    has_lockfile = False
    
    if lockfile.exists():
        # Lockfile exists - check if process is still alive
        try:
            with open(lockfile, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            try:
                os.kill(pid, 0)  # Signal 0 doesn't kill, just checks existence
                log.debug(f"Lockfile exists for PID {pid} which is still running")
                has_lockfile = True
            except OSError:
                # Process doesn't exist - stale lockfile
                log.warning(f"Stale lockfile found for PID {pid}, cleaning up")
                lockfile.unlink()
                has_lockfile = False
        except (ValueError, IOError):
            # Invalid lockfile
            log.warning(f"Invalid lockfile at {lockfile}, removing")
            try:
                lockfile.unlink()
            except:
                pass
            has_lockfile = False
    
    # Determine what's running
    if has_lockfile and port_in_use:
        return (True, 'lynguine')
    elif port_in_use:
        return (True, 'other')
    else:
        return (False, 'none')


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
        # Update activity timestamp for idle timeout
        global _idle_timeout_manager
        if _idle_timeout_manager:
            _idle_timeout_manager.update_activity()
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Some endpoints don't require body
            body = b''
            request_data = {}
            if content_length > 0:
                body = self.rfile.read(content_length)
                request_data = json.loads(body.decode('utf-8'))
            
            # Route to appropriate handler
            if self.path == '/api/read_data':
                self.handle_read_data(request_data)
            elif self.path == '/api/write_data':
                self.handle_write_data(request_data)
            elif self.path == '/api/compute':
                self.handle_compute(request_data)
            elif self.path == '/api/health':
                self.handle_health()
            elif self.path == '/api/ping':
                self.handle_ping()
            elif self.path == '/api/status':
                self.handle_status()
            # Session endpoints (Phase 5)
            elif self.path == '/api/sessions':
                global _session_manager
                server_session_handlers.handle_create_session(self, _session_manager, request_data)
            elif self.path.startswith('/api/sessions/'):
                global _session_manager
                server_session_handlers.handle_session_operation(self, _session_manager, self.path, request_data)
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
        """Handle GET requests (health check, ping, status, sessions)"""
        # Update activity timestamp for idle timeout
        global _idle_timeout_manager
        if _idle_timeout_manager:
            _idle_timeout_manager.update_activity()
        
        try:
            if self.path == '/api/health':
                self.handle_health()
            elif self.path == '/api/ping':
                self.handle_ping()
            elif self.path == '/api/status':
                self.handle_status()
            elif self.path == '/api/sessions':
                global _session_manager
                server_session_handlers.handle_list_sessions(self, _session_manager)
            elif self.path.startswith('/api/sessions/'):
                global _session_manager
                server_session_handlers.handle_session_operation(self, _session_manager, self.path, {})
            else:
                self.send_error_response(
                    ValueError(f"GET not supported for: {self.path}"), 
                    405
                )
        except Exception as e:
            log.error(f"Error handling GET request: {e}")
            self.send_error_response(e, 500)
    
    def do_DELETE(self):
        """Handle DELETE requests (session deletion)"""
        # Update activity timestamp for idle timeout
        global _idle_timeout_manager
        if _idle_timeout_manager:
            _idle_timeout_manager.update_activity()
        
        try:
            if self.path.startswith('/api/sessions/'):
                global _session_manager
                server_session_handlers.handle_delete_session(self, _session_manager, self.path)
            else:
                self.send_error_response(
                    ValueError(f"DELETE not supported for: {self.path}"), 
                    405
                )
        except Exception as e:
            log.error(f"Error handling DELETE request: {e}")
            self.send_error_response(e, 500)
    
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
    
    def handle_write_data(self, request_data: Dict[str, Any]):
        """
        Handle write_data operation
        
        Expected request format:
        {
            "data": {
                "records": [...],  # DataFrame as records
                "columns": [...]   # optional column order
            },
            "output": {
                "type": "csv",
                "filename": "output.csv",
                ...
            }
        }
        """
        try:
            if 'data' not in request_data or 'output' not in request_data:
                raise ValueError("Request must include both 'data' and 'output'")
            
            # Convert data to DataFrame
            import pandas as pd
            data_spec = request_data['data']
            df = pd.DataFrame.from_records(data_spec['records'])
            
            if 'columns' in data_spec:
                df = df[data_spec['columns']]  # Reorder columns if specified
            
            # Write data using lynguine
            output_spec = request_data['output']
            log.debug(f"Writing data to {output_spec.get('type', 'unknown')}")
            
            io.write_data(df, output_spec)
            
            result = {
                'status': 'success',
                'message': f"Wrote {len(df)} records"
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            log.error(f"Error in handle_write_data: {e}")
            self.send_error_response(e)
    
    def handle_compute(self, request_data: Dict[str, Any]):
        """
        Handle compute operation
        
        Expected request format:
        {
            "operation": "compute_name",
            "data": {
                "records": [...],
                "columns": [...]
            },
            "params": {
                ...  # operation-specific parameters
            }
        }
        """
        try:
            if 'operation' not in request_data:
                raise ValueError("Request must include 'operation'")
            
            operation = request_data['operation']
            log.debug(f"Running compute operation: {operation}")
            
            # Convert data to DataFrame if provided
            import pandas as pd
            if 'data' in request_data:
                data_spec = request_data['data']
                df = pd.DataFrame.from_records(data_spec['records'])
            else:
                df = None
            
            # Get parameters
            params = request_data.get('params', {})
            
            # Execute compute operation
            # TODO: Implement actual compute framework integration
            # For now, return placeholder
            result = {
                'status': 'success',
                'operation': operation,
                'message': f"Compute operation '{operation}' completed",
                'result': None  # Would contain actual compute results
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            log.error(f"Error in handle_compute: {e}")
            self.send_error_response(e)
    
    def handle_status(self):
        """
        Status endpoint with server diagnostics
        
        Returns detailed information about server state, uptime, and statistics.
        """
        global _idle_timeout_manager
        
        try:
            import psutil
            import time
            
            # Get process info
            process = psutil.Process(os.getpid())
            
            # Calculate uptime
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            
            status_info = {
                'status': 'ok',
                'server': 'lynguine-server',
                'version': '0.2.0',  # Phase 2
                'pid': os.getpid(),
                'uptime_seconds': uptime_seconds,
                'memory': {
                    'rss_mb': process.memory_info().rss / 1024 / 1024,
                    'percent': process.memory_percent()
                },
                'cpu_percent': process.cpu_percent(interval=0.1),
                'endpoints': [
                    'GET  /api/health',
                    'GET  /api/ping',
                    'GET  /api/status',
                    'POST /api/read_data',
                    'POST /api/write_data',
                    'POST /api/compute'
                ]
            }
            
            # Add idle timeout info if enabled
            if _idle_timeout_manager:
                status_info['idle_timeout'] = {
                    'enabled': True,
                    'timeout_seconds': _idle_timeout_manager.timeout_seconds,
                    'idle_seconds': _idle_timeout_manager.get_idle_time(),
                    'remaining_seconds': max(0, _idle_timeout_manager.timeout_seconds - _idle_timeout_manager.get_idle_time())
                }
            else:
                status_info['idle_timeout'] = {'enabled': False}
            
            self.send_json_response(status_info)
            
        except ImportError:
            # psutil not available, return basic status
            basic_status = {
                'status': 'ok',
                'server': 'lynguine-server',
                'version': '0.2.0',
                'pid': os.getpid(),
                'message': 'Install psutil for detailed diagnostics'
            }
            
            # Add idle timeout info if enabled
            if _idle_timeout_manager:
                basic_status['idle_timeout'] = {
                    'enabled': True,
                    'timeout_seconds': _idle_timeout_manager.timeout_seconds,
                    'idle_seconds': _idle_timeout_manager.get_idle_time(),
                    'remaining_seconds': max(0, _idle_timeout_manager.timeout_seconds - _idle_timeout_manager.get_idle_time())
                }
            else:
                basic_status['idle_timeout'] = {'enabled': False}
            
            self.send_json_response(basic_status)
        except Exception as e:
            log.error(f"Error in handle_status: {e}")
            self.send_error_response(e)


def run_server(host: str = '127.0.0.1', port: int = 8765, idle_timeout: int = 0):
    """
    Start the lynguine HTTP server
    
    Checks if a server is already running on the specified host:port
    and prevents duplicate instances.
    
    :param host: Host address to bind to (default: 127.0.0.1 for localhost only)
    :param port: Port number to listen on (default: 8765)
    :param idle_timeout: Seconds of inactivity before auto-shutdown (0 = disabled)
    :raises RuntimeError: If port is already in use
    """
    # Check if port is already in use
    is_running, server_type = check_server_running(host, port)
    
    if is_running:
        if server_type == 'lynguine':
            error_msg = (
                f"A lynguine server is already running on http://{host}:{port}\n"
                f"\n"
                f"To connect to the existing server:\n"
                f"  from lynguine.client import ServerClient\n"
                f"  client = ServerClient('http://{host}:{port}')\n"
                f"\n"
                f"To start a new server on a different port:\n"
                f"  python -m lynguine.server --port {port + 1}"
            )
        else:  # server_type == 'other'
            error_msg = (
                f"Port {port} is already in use by another application on {host}\n"
                f"\n"
                f"To start lynguine server on a different port:\n"
                f"  python -m lynguine.server --port {port + 1}\n"
                f"\n"
                f"Or stop the other application using port {port}"
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
    
    # Setup idle timeout if enabled
    global _idle_timeout_manager
    if idle_timeout > 0:
        def shutdown_callback():
            """Callback to trigger server shutdown on idle timeout"""
            httpd.shutdown()
        
        _idle_timeout_manager = IdleTimeoutManager(idle_timeout, shutdown_callback)
    
    # Setup session manager (Phase 5)
    global _session_manager
    _session_manager = SessionManager()
    _session_manager.start_cleanup_thread()
    log.info("Session manager initialized with crash recovery")
    
    print(f"Lynguine Server Mode (Phase 5)")
    print(f"==============================")
    print(f"Server starting on http://{host}:{port}")
    print(f"PID: {os.getpid()}")
    if idle_timeout > 0:
        print(f"Idle timeout: {idle_timeout}s ({idle_timeout/60:.1f} minutes)")
    print(f"Session recovery: enabled")
    print(f"Press Ctrl+C to stop")
    print()
    print(f"Available endpoints:")
    print(f"  GET    /api/health                       - Health check")
    print(f"  GET    /api/ping                         - Connectivity test")
    print(f"  GET    /api/status                       - Server status and diagnostics")
    print(f"  POST   /api/read_data                    - Read data via lynguine")
    print(f"  POST   /api/write_data                   - Write data via lynguine")
    print(f"  POST   /api/compute                      - Run compute operations")
    print(f"")
    print(f"  Phase 5: Stateful Sessions (CustomDataFrame API):")
    print(f"  POST   /api/sessions                     - Create session")
    print(f"  GET    /api/sessions                     - List sessions")
    print(f"  GET    /api/sessions/{{id}}                - Get session info")
    print(f"  DELETE /api/sessions/{{id}}                - Delete session")
    print(f"  POST   /api/sessions/{{id}}/set_index      - Set current row focus")
    print(f"  GET    /api/sessions/{{id}}/get_index      - Get current row focus")
    print(f"  POST   /api/sessions/{{id}}/set_column     - Set current column focus")
    print(f"  GET    /api/sessions/{{id}}/get_column     - Get current column focus")
    print(f"  GET    /api/sessions/{{id}}/get_value      - Get value at focus")
    print(f"  POST   /api/sessions/{{id}}/set_value      - Set value at focus")
    print(f"  POST   /api/sessions/{{id}}/get_value_at   - Get value at (index, column)")
    print(f"  GET    /api/sessions/{{id}}/get_shape      - Get DataFrame shape")
    print(f"  GET    /api/sessions/{{id}}/get_columns    - Get all columns")
    print(f"  ... (see docs for full CustomDataFrame API)")
    print()
    
    log.info(f"Server started on {host}:{port} (PID: {os.getpid()}, idle_timeout: {idle_timeout}s)")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
        log.info("Server stopped by user")
    finally:
        # Cleanup
        if _idle_timeout_manager:
            _idle_timeout_manager.stop()
        if _session_manager:
            _session_manager.shutdown()
        cleanup_lockfile()
        print("Server stopped.")


if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Lynguine Server Mode (Phase 2)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8765, help='Port to listen on (default: 8765)')
    parser.add_argument('--idle-timeout', type=int, default=0, 
                        help='Seconds of inactivity before auto-shutdown (0 = disabled, default: 0)')
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, idle_timeout=args.idle_timeout)

