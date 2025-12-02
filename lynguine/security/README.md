# Lynguine Security Module

Enterprise-grade secure credential management, access control, and auditing for Lynguine.

## Quick Start

### Installation

```bash
# Basic installation (environment variables only)
pip install lynguine

# Full installation (with encrypted storage)
pip install lynguine cryptography
```

### Basic Usage

```python
from lynguine.security import set_credential, get_credential

# Store a credential
set_credential("my_api_key", {"value": "secret-key-123"})

# Retrieve a credential
creds = get_credential("my_api_key")
print(creds["value"])
```

### Configuration File Integration

Update your `_lynguine.yml` or `machine.yml`:

```yaml
# Before (insecure)
google_oauth:
  client_id: your-client-id
  client_secret: your-client-secret

# After (secure)
google_oauth: ${credential:google_sheets_oauth}
```

## Features

### 🔐 Secure Storage
- **Environment Variables**: Fast, CI/CD-friendly
- **Encrypted Files**: AES encryption with PBKDF2
- **Cloud Vaults**: (Planned) HashiCorp Vault, AWS Secrets Manager

### 🛡️ Access Control
- Role-based access control (RBAC)
- Pattern-based credential matching
- Rate limiting for brute-force protection
- Context-aware permissions

### 📊 Audit Logging
- Comprehensive security event logging
- Query interface for compliance
- Tamper-evident log format
- Configurable retention policies

### 🔍 Secure Logging
- Automatic credential sanitization
- Pattern-based sensitive data detection
- Secure exception handling
- No credential leakage in logs

### 🔄 Migration Tools
- Automated migration from plain-text
- Backup and rollback support
- Validation and health checks
- Migration guides

## Module Structure

```
lynguine/security/
├── __init__.py              # Public API exports
├── credentials.py           # Core credential management
├── access_control.py        # Access control & auditing
├── secure_logging.py        # Secure logging utilities
├── migration.py             # Migration tools
└── README.md               # This file
```

## Core Components

### Credential Management

```python
from lynguine.security import (
    get_credential_manager,
    EnvironmentCredentialProvider,
    EncryptedFileCredentialProvider
)

# Get the global manager
manager = get_credential_manager()

# Or create custom manager
from lynguine.security import CredentialManager
manager = CredentialManager(
    providers=[
        EnvironmentCredentialProvider(prefix="MY_APP"),
        EncryptedFileCredentialProvider(
            storage_path="~/.myapp/creds",
            master_key="secure-password"
        )
    ],
    cache_ttl=300  # 5 minutes
)
```

### Access Control

```python
from lynguine.security import (
    get_access_controller,
    AccessLevel,
    AccessPolicy
)

# Get controller
controller = get_access_controller()

# Authorize access
controller.authorize_access(
    credential_key="prod_database",
    operation=AccessLevel.READ,
    user="data_analyst",
    context="reporting"
)
```

### Audit Logging

```python
from lynguine.security import AuditLogger, AuditEventType

# Create logger
audit = AuditLogger(log_path="~/.myapp/audit.log")

# Query events
events = audit.query_events(
    event_type=AuditEventType.CREDENTIAL_ACCESS,
    user="specific_user",
    limit=100
)
```

### Secure Logging

```python
from lynguine.security import get_secure_logger

# Get secure logger
logger = get_secure_logger(__name__)

# Sensitive data is automatically redacted
logger.info(f"Connecting with password={password}")
# Output: "Connecting with password=***PASSWORD***"
```

## Common Use Cases

### Google Sheets Credentials

```python
from lynguine.security import set_credential

# Store Google OAuth credentials
google_creds = {
    "client_id": "123.apps.googleusercontent.com",
    "client_secret": "your-secret",
    "redirect_uri": "http://localhost:8080"
}
set_credential("google_sheets_oauth", google_creds)
```

Configuration file:
```yaml
google_oauth: ${credential:google_sheets_oauth}
```

### Multi-Environment Setup

```python
import os
from lynguine.security import CredentialManager, EnvironmentCredentialProvider

env = os.environ.get("APP_ENV", "development")

if env == "production":
    # Production: encrypted files
    from lynguine.security import EncryptedFileCredentialProvider
    provider = EncryptedFileCredentialProvider(
        storage_path="/var/app/credentials",
        master_key=os.environ["MASTER_KEY"]
    )
else:
    # Development: environment variables
    provider = EnvironmentCredentialProvider()

manager = CredentialManager(providers=[provider])
```

### Credential Rotation

```python
from lynguine.security import get_credential_manager

manager = get_credential_manager()

# Update credentials
new_creds = {"client_id": "new-id", "client_secret": "new-secret"}
manager.set_credential("api_creds", new_creds)

# Invalidate cache to force refresh
if manager.cache:
    manager.cache.invalidate("api_creds")
```

## API Reference

### Core Functions

- `get_credential(key, credential_type=None, default=None)` - Retrieve credential
- `set_credential(key, value, credential_type=None)` - Store credential
- `get_credential_manager()` - Get global credential manager
- `get_access_controller()` - Get global access controller
- `get_secure_logger(name)` - Get secure logger

### Key Classes

- `CredentialManager` - Central credential management
- `CredentialProvider` - Abstract provider base
- `EnvironmentCredentialProvider` - Environment variable storage
- `EncryptedFileCredentialProvider` - Encrypted file storage
- `CredentialAccessController` - Access control and auditing
- `AuditLogger` - Security event logging
- `CredentialMigrator` - Migration utilities

See individual module docstrings for detailed API documentation.

## Security Best Practices

### ✅ DO:
- Use encrypted file storage for production
- Set restrictive file permissions (0600)
- Rotate credentials regularly
- Monitor audit logs
- Use different credentials per environment
- Store master key securely

### ❌ DON'T:
- Hard-code credentials in source code
- Commit credentials to version control
- Share credentials via insecure channels
- Use weak master keys
- Disable audit logging
- Grant unnecessary permissions

## Examples

### Example 1: Simple API Key Storage

```python
from lynguine.security import set_credential, get_credential

# Store
set_credential("openai_api_key", {"value": "sk-..."})

# Retrieve
api_key = get_credential("openai_api_key")["value"]
```

### Example 2: Database Credentials

```python
from lynguine.security import set_credential

db_creds = {
    "host": "db.example.com",
    "port": 5432,
    "username": "app_user",
    "password": "secure_password",
    "database": "production"
}

set_credential("production_db", db_creds)
```

Configuration:
```yaml
database: ${credential:production_db}
```

### Example 3: OAuth Token Management

```python
from lynguine.security import get_credential_manager

manager = get_credential_manager()

# Store OAuth tokens
oauth_tokens = {
    "access_token": "ya29...",
    "refresh_token": "1//...",
    "expires_at": "2024-12-31T23:59:59Z"
}

manager.set_credential("user_oauth", oauth_tokens)

# Register validator for OAuth tokens
def validate_oauth(cred):
    required = ["access_token", "refresh_token"]
    return all(k in cred.get("value", {}) for k in required)

manager.register_validator("oauth", validate_oauth)
```

## Migration

For migrating existing credentials, see the [Migration Guide](../../../docs/security/SECURE_CREDENTIALS.md#migration).

Quick migration:

```python
from lynguine.security import CredentialMigrator

migrator = CredentialMigrator()
report = migrator.migrate_google_sheets_credentials(
    config_file="~/.lynguine/config/machine.yml",
    dry_run=False
)
print(f"Migrated {len(report['migrated'])} credentials")
```

## Testing

Run tests:

```bash
# All security tests
pytest lynguine/tests/test_security_credentials.py -v

# Specific test class
pytest lynguine/tests/test_security_credentials.py::TestCredentialManager -v

# With coverage
pytest lynguine/tests/test_security_credentials.py --cov=lynguine.security
```

## Documentation

- **User Guide**: [docs/security/SECURE_CREDENTIALS.md](../../../docs/security/SECURE_CREDENTIALS.md)
- **Implementation Summary**: [docs/security/IMPLEMENTATION_SUMMARY.md](../../../docs/security/IMPLEMENTATION_SUMMARY.md)
- **API Documentation**: See module docstrings

## Dependencies

### Required:
- Python 3.6+
- PyYAML

### Optional:
- cryptography >= 3.0 (for encrypted file storage)

## License

This module is part of Lynguine and is licensed under the same license as the main project.

## Support

- **Issues**: [GitHub Issues](https://github.com/lawrennd/lynguine/issues)
- **Documentation**: [Lynguine Docs](https://lynguine.readthedocs.io)
- **Security Policy**: See SECURITY.md

## Contributing

Contributions welcome! Please:
1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## Version

**Current Version**: 1.0.0

## Authors

Lynguine Security Team

---

**⚠️ Security Notice**: This module handles sensitive credentials. Always follow security best practices and report security issues responsibly.

