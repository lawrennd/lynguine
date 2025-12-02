"""
Secure logging and error handling for credential operations.

This module provides utilities to prevent credential leakage in logs and
error messages while maintaining useful debugging information.
"""

import logging
import re
import traceback
from typing import Any, Dict, List, Optional, Pattern
import sys


# Patterns that might indicate sensitive information
SENSITIVE_PATTERNS = [
    # API Keys and tokens
    (re.compile(r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', re.IGNORECASE), '***API_KEY***'),
    (re.compile(r'["\']?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', re.IGNORECASE), '***TOKEN***'),
    (re.compile(r'["\']?secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', re.IGNORECASE), '***SECRET***'),
    
    # Passwords
    (re.compile(r'["\']?password["\']?\s*[:=]\s*["\']?([^\s"\']{6,})["\']?', re.IGNORECASE), '***PASSWORD***'),
    (re.compile(r'["\']?passwd["\']?\s*[:=]\s*["\']?([^\s"\']{6,})["\']?', re.IGNORECASE), '***PASSWORD***'),
    (re.compile(r'["\']?pwd["\']?\s*[:=]\s*["\']?([^\s"\']{6,})["\']?', re.IGNORECASE), '***PASSWORD***'),
    
    # OAuth and authentication
    (re.compile(r'["\']?client[_-]?secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', re.IGNORECASE), '***CLIENT_SECRET***'),
    (re.compile(r'["\']?client[_-]?id["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', re.IGNORECASE), '***CLIENT_ID***'),
    (re.compile(r'["\']?access[_-]?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', re.IGNORECASE), '***ACCESS_TOKEN***'),
    (re.compile(r'["\']?refresh[_-]?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', re.IGNORECASE), '***REFRESH_TOKEN***'),
    
    # Private keys
    (re.compile(r'-----BEGIN [A-Z\s]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z\s]+ PRIVATE KEY-----', re.MULTILINE), '***PRIVATE_KEY***'),
    (re.compile(r'["\']?private[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9+/=\n\r]{100,})["\']?', re.IGNORECASE), '***PRIVATE_KEY***'),
    
    # Connection strings
    (re.compile(r'[a-z]+://[^:]+:([^@]+)@', re.IGNORECASE), '***PASSWORD***'),
    
    # Email addresses (sometimes sensitive in context)
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '***EMAIL***'),
]


class SanitizingFormatter(logging.Formatter):
    """
    Logging formatter that sanitizes sensitive information.
    
    This formatter automatically redacts sensitive patterns like API keys,
    passwords, and tokens from log messages.
    """
    
    def __init__(
        self,
        fmt: str = None,
        datefmt: str = None,
        style: str = '%',
        additional_patterns: List[tuple] = None
    ):
        """
        Initialize the sanitizing formatter.
        
        :param fmt: Log format string
        :type fmt: str
        :param datefmt: Date format string
        :type datefmt: str
        :param style: Format style ('%', '{', or '$')
        :type style: str
        :param additional_patterns: Additional (pattern, replacement) tuples
        :type additional_patterns: List[tuple]
        """
        super().__init__(fmt, datefmt, style)
        self.patterns = SENSITIVE_PATTERNS.copy()
        if additional_patterns:
            self.patterns.extend(additional_patterns)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with sanitization.
        
        :param record: Log record to format
        :type record: logging.LogRecord
        :return: Formatted and sanitized log message
        :rtype: str
        """
        # Sanitize the message
        if record.msg:
            record.msg = self.sanitize(str(record.msg))
        
        # Sanitize arguments
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.sanitize(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.sanitize(str(arg)) for arg in record.args)
        
        return super().format(record)
    
    def sanitize(self, text: str) -> str:
        """
        Sanitize text by removing sensitive patterns.
        
        :param text: Text to sanitize
        :type text: str
        :return: Sanitized text
        :rtype: str
        """
        if not isinstance(text, str):
            return text
        
        sanitized = text
        for pattern, replacement in self.patterns:
            if isinstance(pattern, Pattern):
                sanitized = pattern.sub(replacement, sanitized)
            else:
                # String pattern
                sanitized = sanitized.replace(pattern, replacement)
        
        return sanitized


class SecureExceptionHandler:
    """
    Exception handler that sanitizes sensitive information from exceptions.
    """
    
    def __init__(self):
        """Initialize the secure exception handler."""
        self.logger = logging.getLogger(f"{__name__}.SecureExceptionHandler")
    
    def sanitize_exception(self, exc: Exception) -> Exception:
        """
        Sanitize an exception's message.
        
        :param exc: The exception to sanitize
        :type exc: Exception
        :return: Exception with sanitized message
        :rtype: Exception
        """
        if exc.args:
            sanitized_args = []
            for arg in exc.args:
                if isinstance(arg, str):
                    sanitized_args.append(self.sanitize_text(arg))
                else:
                    sanitized_args.append(arg)
            exc.args = tuple(sanitized_args)
        return exc
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing sensitive patterns.
        
        :param text: Text to sanitize
        :type text: str
        :return: Sanitized text
        :rtype: str
        """
        if not isinstance(text, str):
            return text
        
        sanitized = text
        for pattern, replacement in SENSITIVE_PATTERNS:
            if isinstance(pattern, Pattern):
                sanitized = pattern.sub(replacement, sanitized)
        
        return sanitized
    
    def sanitize_traceback(self, tb_str: str) -> str:
        """
        Sanitize a traceback string.
        
        :param tb_str: Traceback string
        :type tb_str: str
        :return: Sanitized traceback
        :rtype: str
        """
        return self.sanitize_text(tb_str)
    
    def format_exception(
        self,
        exc_type: type,
        exc_value: Exception,
        exc_traceback: Any
    ) -> str:
        """
        Format an exception with sanitized information.
        
        :param exc_type: Exception type
        :type exc_type: type
        :param exc_value: Exception instance
        :type exc_value: Exception
        :param exc_traceback: Exception traceback
        :return: Formatted and sanitized exception
        :rtype: str
        """
        # Get the traceback as string
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = ''.join(tb_lines)
        
        # Sanitize the traceback
        sanitized_tb = self.sanitize_traceback(tb_str)
        
        return sanitized_tb


def setup_secure_logging(
    logger: logging.Logger = None,
    level: int = logging.INFO,
    format_string: str = None,
    additional_patterns: List[tuple] = None
) -> logging.Logger:
    """
    Set up secure logging with sanitization for a logger.
    
    :param logger: Logger to configure (None for root logger)
    :type logger: logging.Logger
    :param level: Logging level
    :type level: int
    :param format_string: Custom format string
    :type format_string: str
    :param additional_patterns: Additional sanitization patterns
    :type additional_patterns: List[tuple]
    :return: Configured logger
    :rtype: logging.Logger
    """
    if logger is None:
        logger = logging.getLogger()
    
    # Set level
    logger.setLevel(level)
    
    # Create sanitizing formatter
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = SanitizingFormatter(
        fmt=format_string,
        additional_patterns=additional_patterns
    )
    
    # Configure handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Update existing handlers
        for handler in logger.handlers:
            handler.setFormatter(formatter)
    
    return logger


def sanitize_dict(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Sanitize a dictionary by redacting sensitive keys.
    
    :param data: Dictionary to sanitize
    :type data: Dict[str, Any]
    :param sensitive_keys: List of keys to redact (case-insensitive)
    :type sensitive_keys: List[str]
    :return: Sanitized dictionary
    :rtype: Dict[str, Any]
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
            'private_key', 'privatekey', 'client_secret', 'clientsecret',
            'access_token', 'accesstoken', 'refresh_token', 'refreshtoken',
            'auth', 'authorization', 'credential', 'credentials'
        ]
    
    # Normalize sensitive keys to lowercase for comparison
    sensitive_keys_lower = [k.lower() for k in sensitive_keys]
    
    def sanitize_value(key: str, value: Any) -> Any:
        """Sanitize a value based on its key."""
        key_lower = key.lower()
        
        # Check if key is sensitive
        if any(sens_key in key_lower for sens_key in sensitive_keys_lower):
            if isinstance(value, str):
                # Show only first/last chars if long enough
                if len(value) > 8:
                    return f"{value[:2]}***{value[-2:]}"
                else:
                    return "***"
            else:
                return "***REDACTED***"
        
        # Recursively sanitize nested structures
        if isinstance(value, dict):
            return sanitize_dict(value, sensitive_keys)
        elif isinstance(value, list):
            return [sanitize_value(f"{key}[{i}]", item) for i, item in enumerate(value)]
        else:
            return value
    
    # Create sanitized copy
    sanitized = {}
    for key, value in data.items():
        sanitized[key] = sanitize_value(key, value)
    
    return sanitized


def secure_repr(obj: Any, max_len: int = 100) -> str:
    """
    Get a secure string representation of an object.
    
    This function attempts to sanitize the repr() output to avoid
    exposing sensitive information.
    
    :param obj: Object to represent
    :type obj: Any
    :param max_len: Maximum length of representation
    :type max_len: int
    :return: Secure representation
    :rtype: str
    """
    try:
        if isinstance(obj, dict):
            sanitized = sanitize_dict(obj)
            repr_str = repr(sanitized)
        elif isinstance(obj, str):
            # Sanitize string directly
            formatter = SanitizingFormatter()
            repr_str = formatter.sanitize(repr(obj))
        else:
            repr_str = repr(obj)
        
        # Truncate if too long
        if len(repr_str) > max_len:
            repr_str = repr_str[:max_len] + "..."
        
        return repr_str
    except Exception:
        return f"<{type(obj).__name__} object>"


class SecureLogger:
    """
    Wrapper around standard logger with automatic sanitization.
    """
    
    def __init__(self, name: str, logger: logging.Logger = None):
        """
        Initialize secure logger.
        
        :param name: Logger name
        :type name: str
        :param logger: Underlying logger (creates new if None)
        :type logger: logging.Logger
        """
        self.name = name
        if logger is None:
            self.logger = setup_secure_logging(logging.getLogger(name))
        else:
            self.logger = logger
        self.formatter = SanitizingFormatter()
    
    def _sanitize_args(self, *args) -> tuple:
        """Sanitize log arguments."""
        return tuple(self.formatter.sanitize(str(arg)) for arg in args)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with sanitization."""
        sanitized_msg = self.formatter.sanitize(str(msg))
        sanitized_args = self._sanitize_args(*args)
        self.logger.debug(sanitized_msg, *sanitized_args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message with sanitization."""
        sanitized_msg = self.formatter.sanitize(str(msg))
        sanitized_args = self._sanitize_args(*args)
        self.logger.info(sanitized_msg, *sanitized_args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with sanitization."""
        sanitized_msg = self.formatter.sanitize(str(msg))
        sanitized_args = self._sanitize_args(*args)
        self.logger.warning(sanitized_msg, *sanitized_args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message with sanitization."""
        sanitized_msg = self.formatter.sanitize(str(msg))
        sanitized_args = self._sanitize_args(*args)
        self.logger.error(sanitized_msg, *sanitized_args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with sanitization."""
        sanitized_msg = self.formatter.sanitize(str(msg))
        sanitized_args = self._sanitize_args(*args)
        self.logger.critical(sanitized_msg, *sanitized_args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception with sanitized traceback."""
        sanitized_msg = self.formatter.sanitize(str(msg))
        sanitized_args = self._sanitize_args(*args)
        
        # Get and sanitize current exception
        exc_info = sys.exc_info()
        if exc_info[0] is not None:
            handler = SecureExceptionHandler()
            sanitized_tb = handler.format_exception(*exc_info)
            # Log with the sanitized traceback
            self.logger.error(f"{sanitized_msg}\n{sanitized_tb}", *sanitized_args)
        else:
            self.logger.error(sanitized_msg, *sanitized_args, **kwargs)


def get_secure_logger(name: str) -> SecureLogger:
    """
    Get or create a secure logger.
    
    :param name: Logger name
    :type name: str
    :return: Secure logger instance
    :rtype: SecureLogger
    """
    return SecureLogger(name)

