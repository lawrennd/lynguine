"""
Session Manager for stateful lynguine server mode.

Manages CustomDataFrame instances loaded from interface files,
providing focus-based navigation and data access with session
persistence for crash recovery.
"""
import os
import time
import uuid
import pickle
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import threading

from .config.interface import Interface
from .assess.data import CustomDataFrame
from .log import Logger
from .config.context import Context

cntxt = Context(name="lynguine")
log = Logger(
    name=__name__,
    level=cntxt._data["logging"]["level"],
    filename=cntxt._data["logging"]["filename"],
)


class Session:
    """Represents a stateful data session with CustomDataFrame.
    
    Maintains focus state (current index, column, selector, subindex) and
    provides the CustomDataFrame API over HTTP.
    """
    
    def __init__(
        self,
        session_id: str,
        cdf: CustomDataFrame,
        interface_file: str,
        directory: str,
        interface_field: Optional[str] = None,
        timeout: int = 3600,
        created_time: Optional[float] = None
    ):
        self.session_id = session_id
        self.cdf = cdf
        self.interface_file = interface_file
        self.directory = directory
        self.interface_field = interface_field
        self.timeout = timeout
        self.created_time = created_time or time.time()
        self.last_accessed = time.time()
        
        # Track memory usage
        import sys
        self.memory_mb = sys.getsizeof(self.cdf) / (1024 * 1024)
        
        log.info(f"Created session {session_id} from {interface_file}")
    
    def update_access_time(self):
        """Update last accessed time"""
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if session has expired based on timeout"""
        if self.timeout == 0:
            return False
        return (time.time() - self.last_accessed) > self.timeout
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get session metadata"""
        return {
            'session_id': self.session_id,
            'interface_file': self.interface_file,
            'directory': self.directory,
            'interface_field': self.interface_field,
            'shape': self.cdf.get_shape(),
            'columns': list(self.cdf.columns),
            'memory_mb': round(self.memory_mb, 2),
            'created_time': self.created_time,
            'last_accessed': self.last_accessed,
            'timeout': self.timeout,
            'age_seconds': round(time.time() - self.created_time, 2),
            'idle_seconds': round(time.time() - self.last_accessed, 2),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize session for persistence (without CustomDataFrame data)"""
        return {
            'session_id': self.session_id,
            'interface_file': self.interface_file,
            'directory': self.directory,
            'interface_field': self.interface_field,
            'timeout': self.timeout,
            'created_time': self.created_time,
            'last_accessed': self.last_accessed,
        }


class SessionManager:
    """Manages stateful data sessions with crash recovery.
    
    Maintains in-memory CustomDataFrame instances and persists session
    metadata for recovery after server crashes.
    """
    
    def __init__(
        self,
        persistence_dir: Optional[str] = None,
        max_sessions: int = 100,
        max_memory_mb: int = 10000,  # 10GB default
        cleanup_interval: int = 60,  # Check every minute
    ):
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.max_memory_mb = max_memory_mb
        self.cleanup_interval = cleanup_interval
        
        # Setup persistence directory
        if persistence_dir is None:
            persistence_dir = os.path.join(os.path.expanduser('~'), '.lynguine', 'sessions')
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = None
        self.cleanup_running = False
        
        log.info(f"SessionManager initialized with persistence at {self.persistence_dir}")
        
        # Attempt to recover sessions from previous run
        self._recover_sessions()
    
    def _get_persistence_file(self) -> Path:
        """Get the main persistence file path"""
        return self.persistence_dir / 'sessions.json'
    
    def _save_metadata(self):
        """Save session metadata to disk for crash recovery"""
        try:
            metadata = {
                'sessions': [s.to_dict() for s in self.sessions.values()],
                'saved_at': time.time(),
            }
            
            persistence_file = self._get_persistence_file()
            tmp_file = persistence_file.with_suffix('.tmp')
            
            # Write to temp file first, then atomic rename
            with open(tmp_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            tmp_file.replace(persistence_file)
            log.debug(f"Saved {len(self.sessions)} session(s) metadata to {persistence_file}")
            
        except Exception as e:
            log.error(f"Failed to save session metadata: {e}")
    
    def _recover_sessions(self):
        """Recover sessions from previous server run"""
        persistence_file = self._get_persistence_file()
        
        if not persistence_file.exists():
            log.debug("No previous sessions to recover")
            return
        
        try:
            with open(persistence_file, 'r') as f:
                metadata = json.load(f)
            
            recovered_count = 0
            failed_count = 0
            
            for session_data in metadata.get('sessions', []):
                try:
                    # Recreate session by reloading interface file
                    session = self.create_session(
                        interface_file=session_data['interface_file'],
                        directory=session_data['directory'],
                        interface_field=session_data.get('interface_field'),
                        timeout=session_data['timeout'],
                        session_id=session_data['session_id'],  # Preserve original ID
                        created_time=session_data['created_time'],
                    )
                    recovered_count += 1
                    log.info(f"Recovered session {session.session_id}")
                    
                except Exception as e:
                    failed_count += 1
                    log.warning(f"Failed to recover session {session_data['session_id']}: {e}")
            
            if recovered_count > 0:
                log.info(f"Session recovery complete: {recovered_count} recovered, {failed_count} failed")
            
        except Exception as e:
            log.error(f"Failed to recover sessions: {e}")
    
    def start_cleanup_thread(self):
        """Start background thread for session cleanup"""
        if self.cleanup_thread is not None and self.cleanup_thread.is_alive():
            return
        
        self.cleanup_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        log.info("Session cleanup thread started")
    
    def stop_cleanup_thread(self):
        """Stop background cleanup thread"""
        self.cleanup_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        log.info("Session cleanup thread stopped")
    
    def _cleanup_loop(self):
        """Background loop to cleanup expired sessions"""
        while self.cleanup_running:
            try:
                time.sleep(self.cleanup_interval)
                self.cleanup_expired_sessions()
            except Exception as e:
                log.error(f"Error in cleanup loop: {e}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with self.lock:
            expired = [sid for sid, session in self.sessions.items() if session.is_expired()]
            
            for session_id in expired:
                self.delete_session(session_id)
                log.info(f"Cleaned up expired session {session_id}")
            
            if expired:
                self._save_metadata()
    
    def create_session(
        self,
        interface_file: str,
        directory: str = '.',
        interface_field: Optional[str] = None,
        timeout: int = 3600,
        session_id: Optional[str] = None,
        created_time: Optional[float] = None,
    ) -> Session:
        """Create a new session by loading interface file.
        
        Args:
            interface_file: Path to lynguine interface YAML file
            directory: Directory for resolving relative paths
            interface_field: Optional field within interface
            timeout: Session timeout in seconds (0 = no timeout)
            session_id: Optional session ID (for recovery)
            created_time: Optional creation time (for recovery)
        
        Returns:
            Session object
        
        Raises:
            ValueError: If max sessions or memory limit exceeded
            FileNotFoundError: If interface file not found
        """
        with self.lock:
            # Check limits
            if len(self.sessions) >= self.max_sessions:
                raise ValueError(
                    f"Maximum number of sessions ({self.max_sessions}) reached. "
                    "Delete existing sessions or increase limit."
                )
            
            total_memory = sum(s.memory_mb for s in self.sessions.values())
            if total_memory >= self.max_memory_mb:
                raise ValueError(
                    f"Maximum memory limit ({self.max_memory_mb}MB) reached. "
                    f"Current: {total_memory:.1f}MB. Delete sessions to free memory."
                )
            
            # Generate session ID if not provided
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Load interface and create CustomDataFrame
            full_path = os.path.join(directory, interface_file)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Interface file not found: {full_path}")
            
            log.info(f"Loading interface from {full_path}")
            interface = Interface.from_file(interface_file, directory=directory)
            
            # Create CustomDataFrame from interface
            cdf = CustomDataFrame.from_flow(interface)
            
            # Create session
            session = Session(
                session_id=session_id,
                cdf=cdf,
                interface_file=interface_file,
                directory=directory,
                interface_field=interface_field,
                timeout=timeout,
                created_time=created_time,
            )
            
            self.sessions[session_id] = session
            
            # Save metadata for crash recovery
            self._save_metadata()
            
            log.info(
                f"Created session {session_id}: "
                f"shape={session.cdf.get_shape()}, memory={session.memory_mb:.2f}MB"
            )
            
            return session
    
    def get_session(self, session_id: str) -> Session:
        """Get session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            Session object
        
        Raises:
            KeyError: If session not found
        """
        with self.lock:
            if session_id not in self.sessions:
                raise KeyError(f"Session not found: {session_id}")
            
            session = self.sessions[session_id]
            session.update_access_time()
            return session
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with metadata"""
        with self.lock:
            return [s.get_metadata() for s in self.sessions.values()]
    
    def delete_session(self, session_id: str):
        """Delete a session.
        
        Args:
            session_id: Session ID to delete
        
        Raises:
            KeyError: If session not found
        """
        with self.lock:
            if session_id not in self.sessions:
                raise KeyError(f"Session not found: {session_id}")
            
            del self.sessions[session_id]
            
            # Update persistence
            self._save_metadata()
            
            log.info(f"Deleted session {session_id}")
    
    def delete_all_sessions(self):
        """Delete all sessions"""
        with self.lock:
            count = len(self.sessions)
            self.sessions.clear()
            self._save_metadata()
            log.info(f"Deleted all {count} session(s)")
    
    def get_total_memory(self) -> float:
        """Get total memory usage across all sessions in MB"""
        with self.lock:
            return sum(s.memory_mb for s in self.sessions.values())
    
    def shutdown(self):
        """Shutdown session manager"""
        log.info("Shutting down SessionManager")
        self.stop_cleanup_thread()
        self._save_metadata()
        self.sessions.clear()

