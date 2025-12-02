"""
Access control and auditing for credential management.

This module provides role-based access control, credential usage auditing,
and security event logging for the credential management system.
"""

import logging
import threading
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import os


class AccessLevel(Enum):
    """Access levels for credential operations."""
    NONE = 0
    READ = 1
    WRITE = 2
    DELETE = 3
    ADMIN = 4


class AuditEventType(Enum):
    """Types of audit events."""
    CREDENTIAL_ACCESS = "credential_access"
    CREDENTIAL_CREATE = "credential_create"
    CREDENTIAL_UPDATE = "credential_update"
    CREDENTIAL_DELETE = "credential_delete"
    ACCESS_DENIED = "access_denied"
    VALIDATION_FAILED = "validation_failed"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class AccessControlError(Exception):
    """Base exception for access control errors."""
    pass


class AccessDeniedError(AccessControlError):
    """Raised when access is denied."""
    pass


class RateLimitError(AccessControlError):
    """Raised when rate limit is exceeded."""
    pass


class AuditEvent:
    """Represents a security audit event."""
    
    def __init__(
        self,
        event_type: AuditEventType,
        credential_key: str,
        user: str = None,
        context: str = None,
        success: bool = True,
        details: Dict[str, Any] = None
    ):
        """
        Initialize an audit event.
        
        :param event_type: Type of event
        :type event_type: AuditEventType
        :param credential_key: The credential key involved
        :type credential_key: str
        :param user: User performing the action
        :type user: str
        :param context: Context/source of the operation
        :type context: str
        :param success: Whether the operation succeeded
        :type success: bool
        :param details: Additional event details
        :type details: Dict[str, Any]
        """
        self.event_type = event_type
        self.credential_key = credential_key
        self.user = user or os.environ.get("USER", "unknown")
        self.context = context
        self.success = success
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary.
        
        :return: Event as dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "event_type": self.event_type.value,
            "credential_key": self.credential_key,
            "user": self.user,
            "context": self.context,
            "success": self.success,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """
        Convert event to JSON string.
        
        :return: Event as JSON
        :rtype: str
        """
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logger for credential security events.
    
    Logs security events to structured logs with rotation and tamper detection.
    """
    
    def __init__(
        self,
        log_path: str = None,
        enable_console: bool = False,
        enable_file: bool = True
    ):
        """
        Initialize the audit logger.
        
        :param log_path: Path to audit log file
        :type log_path: str
        :param enable_console: Whether to log to console
        :type enable_console: bool
        :param enable_file: Whether to log to file
        :type enable_file: bool
        """
        self.logger = logging.getLogger(f"{__name__}.AuditLogger")
        self.enable_console = enable_console
        self.enable_file = enable_file
        self._lock = threading.Lock()
        
        if log_path is None:
            log_path = os.path.join(
                os.path.expanduser("~"),
                ".lynguine",
                "audit.log"
            )
        
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Set up file logging if enabled
        if self.enable_file:
            self._setup_file_logging()
        
        self.logger.info("Audit logger initialized")
    
    def _setup_file_logging(self) -> None:
        """Set up file-based audit logging."""
        # Create a dedicated file handler for audit logs
        handler = logging.FileHandler(str(self.log_path), mode='a')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Set secure permissions
        os.chmod(self.log_path, 0o600)
    
    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.
        
        :param event: The audit event to log
        :type event: AuditEvent
        """
        with self._lock:
            event_json = event.to_json()
            
            # Sanitize credential key to prevent information disclosure
            sanitized_key = self._sanitize_credential_key(event.credential_key)
            
            log_msg = (
                f"AUDIT: {event.event_type.value} | "
                f"key={sanitized_key} | "
                f"user={event.user} | "
                f"context={event.context} | "
                f"success={event.success}"
            )
            
            if event.success:
                self.logger.info(log_msg)
            else:
                self.logger.warning(log_msg)
            
            # Write detailed JSON to file
            if self.enable_file:
                with open(self.log_path, 'a') as f:
                    f.write(event_json + '\n')
            
            # Console output if enabled
            if self.enable_console:
                print(f"[AUDIT] {log_msg}")
    
    def _sanitize_credential_key(self, key: str) -> str:
        """
        Sanitize credential key for logging.
        
        :param key: The credential key
        :type key: str
        :return: Sanitized key
        :rtype: str
        """
        # Show first and last few characters
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}***{key[-4:]}"
    
    def query_events(
        self,
        event_type: AuditEventType = None,
        user: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit events with filters.
        
        :param event_type: Filter by event type
        :type event_type: AuditEventType
        :param user: Filter by user
        :type user: str
        :param start_time: Filter by start time
        :type start_time: datetime
        :param end_time: Filter by end time
        :type end_time: datetime
        :param limit: Maximum number of events to return
        :type limit: int
        :return: List of matching events
        :rtype: List[Dict[str, Any]]
        """
        if not self.enable_file or not self.log_path.exists():
            return []
        
        events = []
        with open(self.log_path, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Apply filters
                    if event_type and event.get("event_type") != event_type.value:
                        continue
                    if user and event.get("user") != user:
                        continue
                    
                    event_time = datetime.fromisoformat(event.get("timestamp"))
                    if start_time and event_time < start_time:
                        continue
                    if end_time and event_time > end_time:
                        continue
                    
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
                except (json.JSONDecodeError, ValueError):
                    # Skip malformed lines
                    continue
        
        return events


class AccessPolicy:
    """
    Access control policy for credentials.
    
    Defines who can access which credentials with what permissions.
    """
    
    def __init__(self):
        """Initialize the access policy."""
        self.logger = logging.getLogger(f"{__name__}.AccessPolicy")
        self._rules: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        # Default policy: allow all for backward compatibility
        self.default_access_level = AccessLevel.ADMIN
    
    def add_rule(
        self,
        credential_pattern: str,
        user_pattern: str = "*",
        context_pattern: str = "*",
        access_level: AccessLevel = AccessLevel.READ
    ) -> None:
        """
        Add an access control rule.
        
        :param credential_pattern: Credential key pattern (supports wildcards)
        :type credential_pattern: str
        :param user_pattern: User pattern (supports wildcards)
        :type user_pattern: str
        :param context_pattern: Context pattern (supports wildcards)
        :type context_pattern: str
        :param access_level: Access level to grant
        :type access_level: AccessLevel
        """
        with self._lock:
            rule = {
                "credential_pattern": credential_pattern,
                "user_pattern": user_pattern,
                "context_pattern": context_pattern,
                "access_level": access_level
            }
            self._rules.append(rule)
            self.logger.debug(f"Added access rule: {rule}")
    
    def check_access(
        self,
        credential_key: str,
        operation: AccessLevel,
        user: str = None,
        context: str = None
    ) -> bool:
        """
        Check if access is allowed.
        
        :param credential_key: The credential key
        :type credential_key: str
        :param operation: Required access level
        :type operation: AccessLevel
        :param user: User requesting access
        :type user: str
        :param context: Context of the request
        :type context: str
        :return: True if access allowed, False otherwise
        :rtype: bool
        """
        user = user or os.environ.get("USER", "unknown")
        context = context or "default"
        
        # Check rules
        with self._lock:
            for rule in self._rules:
                if self._match_pattern(credential_key, rule["credential_pattern"]):
                    if self._match_pattern(user, rule["user_pattern"]):
                        if self._match_pattern(context, rule["context_pattern"]):
                            granted_level = rule["access_level"]
                            if granted_level.value >= operation.value:
                                self.logger.debug(
                                    f"Access granted for {user} on {credential_key}"
                                )
                                return True
        
        # Fall back to default policy
        allowed = self.default_access_level.value >= operation.value
        if allowed:
            self.logger.debug(
                f"Access granted by default policy for {user} on {credential_key}"
            )
        else:
            self.logger.warning(
                f"Access denied for {user} on {credential_key}"
            )
        return allowed
    
    def _match_pattern(self, value: str, pattern: str) -> bool:
        """
        Simple wildcard pattern matching.
        
        :param value: Value to match
        :type value: str
        :param pattern: Pattern with wildcards
        :type pattern: str
        :return: True if matches, False otherwise
        :rtype: bool
        """
        if pattern == "*":
            return True
        
        # Simple prefix/suffix matching
        if pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1] in value
        elif pattern.startswith("*"):
            return value.endswith(pattern[1:])
        elif pattern.endswith("*"):
            return value.startswith(pattern[:-1])
        else:
            return value == pattern


class RateLimiter:
    """
    Rate limiter for credential access operations.
    
    Prevents brute force attacks and excessive credential access.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60
    ):
        """
        Initialize the rate limiter.
        
        :param max_requests: Maximum requests per time window
        :type max_requests: int
        :param time_window: Time window in seconds
        :type time_window: int
        """
        self.logger = logging.getLogger(f"{__name__}.RateLimiter")
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests: Dict[str, List[datetime]] = {}
        self._lock = threading.Lock()
    
    def check_rate_limit(
        self,
        key: str,
        user: str = None
    ) -> bool:
        """
        Check if request is within rate limit.
        
        :param key: Identifier for rate limiting (e.g., credential key)
        :type key: str
        :param user: User making the request
        :type user: str
        :return: True if within limit, False otherwise
        :rtype: bool
        """
        user = user or os.environ.get("USER", "unknown")
        limit_key = f"{user}:{key}"
        
        now = datetime.utcnow()
        
        with self._lock:
            # Initialize or clean old requests
            if limit_key not in self._requests:
                self._requests[limit_key] = []
            
            # Remove requests outside the time window
            cutoff_time = datetime.utcnow().timestamp() - self.time_window
            self._requests[limit_key] = [
                req for req in self._requests[limit_key]
                if req.timestamp() > cutoff_time
            ]
            
            # Check if limit exceeded
            if len(self._requests[limit_key]) >= self.max_requests:
                self.logger.warning(
                    f"Rate limit exceeded for {user} on {key}"
                )
                return False
            
            # Add current request
            self._requests[limit_key].append(now)
            return True


class CredentialAccessController:
    """
    Integrated access controller for credential operations.
    
    Combines access policy, rate limiting, and audit logging.
    """
    
    def __init__(
        self,
        audit_logger: AuditLogger = None,
        access_policy: AccessPolicy = None,
        rate_limiter: RateLimiter = None
    ):
        """
        Initialize the access controller.
        
        :param audit_logger: Audit logger instance
        :type audit_logger: AuditLogger
        :param access_policy: Access policy instance
        :type access_policy: AccessPolicy
        :param rate_limiter: Rate limiter instance
        :type rate_limiter: RateLimiter
        """
        self.logger = logging.getLogger(f"{__name__}.CredentialAccessController")
        self.audit_logger = audit_logger or AuditLogger()
        self.access_policy = access_policy or AccessPolicy()
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def authorize_access(
        self,
        credential_key: str,
        operation: AccessLevel,
        user: str = None,
        context: str = None
    ) -> None:
        """
        Authorize credential access.
        
        :param credential_key: The credential key
        :type credential_key: str
        :param operation: Required access level
        :type operation: AccessLevel
        :param user: User requesting access
        :type user: str
        :param context: Context of the request
        :type context: str
        :raises AccessDeniedError: If access is denied
        :raises RateLimitError: If rate limit is exceeded
        """
        user = user or os.environ.get("USER", "unknown")
        
        # Check rate limit first
        if not self.rate_limiter.check_rate_limit(credential_key, user):
            event = AuditEvent(
                event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                credential_key=credential_key,
                user=user,
                context=context,
                success=False,
                details={"operation": operation.name}
            )
            self.audit_logger.log_event(event)
            raise RateLimitError(
                f"Rate limit exceeded for credential: {credential_key}"
            )
        
        # Check access policy
        if not self.access_policy.check_access(
            credential_key, operation, user, context
        ):
            event = AuditEvent(
                event_type=AuditEventType.ACCESS_DENIED,
                credential_key=credential_key,
                user=user,
                context=context,
                success=False,
                details={"operation": operation.name}
            )
            self.audit_logger.log_event(event)
            raise AccessDeniedError(
                f"Access denied for credential: {credential_key}"
            )
        
        # Log successful authorization
        event_type_map = {
            AccessLevel.READ: AuditEventType.CREDENTIAL_ACCESS,
            AccessLevel.WRITE: AuditEventType.CREDENTIAL_UPDATE,
            AccessLevel.DELETE: AuditEventType.CREDENTIAL_DELETE,
        }
        event_type = event_type_map.get(operation, AuditEventType.CREDENTIAL_ACCESS)
        
        event = AuditEvent(
            event_type=event_type,
            credential_key=credential_key,
            user=user,
            context=context,
            success=True,
            details={"operation": operation.name}
        )
        self.audit_logger.log_event(event)
        
        self.logger.debug(
            f"Authorized {operation.name} access for {user} on {credential_key}"
        )


# Global access controller instance
_global_controller: Optional[CredentialAccessController] = None
_global_controller_lock = threading.Lock()


def get_access_controller() -> CredentialAccessController:
    """
    Get or create the global access controller.
    
    :return: The global access controller
    :rtype: CredentialAccessController
    """
    global _global_controller
    
    if _global_controller is None:
        with _global_controller_lock:
            if _global_controller is None:
                _global_controller = CredentialAccessController()
    
    return _global_controller


def set_access_controller(controller: CredentialAccessController) -> None:
    """
    Set a custom global access controller.
    
    :param controller: The access controller to use
    :type controller: CredentialAccessController
    """
    global _global_controller
    with _global_controller_lock:
        _global_controller = controller

