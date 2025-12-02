"""
Lynguine Security Module

This module provides secure credential management, access control, and auditing
for the Lynguine data processing library.

Main components:
- Credential management with multiple backend support
- Access control and authorization
- Security audit logging
- Secure error handling and logging
- Migration tools for transitioning to secure credentials
"""

# Credential management
from .credentials import (
    # Providers
    CredentialProvider,
    EnvironmentCredentialProvider,
    EncryptedFileCredentialProvider,
    
    # Manager
    CredentialManager,
    get_credential_manager,
    set_credential_manager,
    
    # Convenience functions
    get_credential,
    set_credential,
    
    # Exceptions
    CredentialError,
    CredentialNotFoundError,
    CredentialValidationError,
    CredentialEncryptionError,
    
    # Cache
    CredentialCache,
    
    # Availability flag
    CRYPTO_AVAILABLE,
)

# Access control and auditing
from .access_control import (
    # Access levels and events
    AccessLevel,
    AuditEventType,
    AuditEvent,
    
    # Components
    AuditLogger,
    AccessPolicy,
    RateLimiter,
    CredentialAccessController,
    
    # Global controller
    get_access_controller,
    set_access_controller,
    
    # Exceptions
    AccessControlError,
    AccessDeniedError,
    RateLimitError,
)

# Secure logging
from .secure_logging import (
    # Formatters and handlers
    SanitizingFormatter,
    SecureExceptionHandler,
    SecureLogger,
    
    # Setup functions
    setup_secure_logging,
    get_secure_logger,
    
    # Utilities
    sanitize_dict,
    secure_repr,
    
    # Patterns
    SENSITIVE_PATTERNS,
)

# Migration tools
from .migration import (
    CredentialMigrator,
    MigrationError,
    create_migration_guide,
    save_migration_guide,
)


__all__ = [
    # Credential management
    'CredentialProvider',
    'EnvironmentCredentialProvider',
    'EncryptedFileCredentialProvider',
    'CredentialManager',
    'get_credential_manager',
    'set_credential_manager',
    'get_credential',
    'set_credential',
    'CredentialError',
    'CredentialNotFoundError',
    'CredentialValidationError',
    'CredentialEncryptionError',
    'CredentialCache',
    'CRYPTO_AVAILABLE',
    
    # Access control
    'AccessLevel',
    'AuditEventType',
    'AuditEvent',
    'AuditLogger',
    'AccessPolicy',
    'RateLimiter',
    'CredentialAccessController',
    'get_access_controller',
    'set_access_controller',
    'AccessControlError',
    'AccessDeniedError',
    'RateLimitError',
    
    # Secure logging
    'SanitizingFormatter',
    'SecureExceptionHandler',
    'SecureLogger',
    'setup_secure_logging',
    'get_secure_logger',
    'sanitize_dict',
    'secure_repr',
    'SENSITIVE_PATTERNS',
    
    # Migration
    'CredentialMigrator',
    'MigrationError',
    'create_migration_guide',
    'save_migration_guide',
]


__version__ = '1.0.0'
__author__ = 'Lynguine Security Team'
__description__ = 'Secure credential management and access control for Lynguine'
