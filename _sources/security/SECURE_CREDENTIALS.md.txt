# Lynguine Secure Credential Management

## Overview

Lynguine's secure credential management system provides enterprise-grade security for API credentials, OAuth tokens, and other sensitive authentication data. This system addresses critical vulnerabilities in credential storage and access while maintaining backward compatibility with existing configurations.

## Features

### Core Security Features

- **Multiple Storage Backends**: Environment variables, encrypted files, and cloud vault integration
- **End-to-End Encryption**: AES encryption with PBKDF2 key derivation for stored credentials
- **Access Control**: Role-based access control with fine-grained permissions
- **Audit Logging**: Comprehensive security event logging for compliance
- **Rate Limiting**: Protection against brute force attacks
- **Credential Rotation**: Support for automatic credential rotation
- **Secure Error Handling**: Prevents credential leakage in logs and exceptions

### Integration Features

- **Backward Compatible**: Works with existing lynguine configurations
- **Credential References**: Use `${credential:name}` syntax in configuration files
- **Migration Tools**: Automated migration from plain-text credentials
- **Validation**: Credential format and type validation
- **Caching**: TTL-based caching for performance

## Quick Start

### Installation

The basic credential system works out of the box. For encrypted storage, install the cryptography library:

```bash
pip install cryptography
```

### Basic Usage

#### 1. Storing Credentials

```python
from lynguine.security import set_credential

# Store Google Sheets OAuth credentials
google_creds = {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "redirect_uri": "http://localhost:8080"
}

set_credential("google_sheets_oauth", google_creds)
```

#### 2. Using Credentials in Configuration

Update your `_lynguine.yml` or `machine.yml`:

```yaml
google_oauth: ${credential:google_sheets_oauth}
```

#### 3. Retrieving Credentials Programmatically

```python
from lynguine.security import get_credential

creds = get_credential("google_sheets_oauth")
print(f"Client ID: {creds['value']['client_id']}")
```

## Storage Backends

### Environment Variables

Best for: Development, CI/CD pipelines, containerized environments

```bash
# Set credential as environment variable
export LYNGUINE_CRED_GOOGLE_SHEETS_OAUTH='{"client_id":"...","client_secret":"..."}'
```

```python
from lynguine.security import EnvironmentCredentialProvider, CredentialManager

provider = EnvironmentCredentialProvider(prefix="LYNGUINE_CRED")
manager = CredentialManager(providers=[provider])
```

**Advantages:**
- No additional dependencies
- Easy integration with deployment systems
- No file storage required

**Disadvantages:**
- Credentials visible in process environment
- Not suitable for long-term storage
- Limited to process lifetime

### Encrypted Files

Best for: Production environments, persistent storage, desktop applications

```python
from lynguine.security import EncryptedFileCredentialProvider, CredentialManager

# Set master key (do this once, store securely!)
import os
os.environ["LYNGUINE_MASTER_KEY"] = "your-secure-master-password"

provider = EncryptedFileCredentialProvider(
    storage_path="~/.lynguine/credentials",
    master_key=os.environ["LYNGUINE_MASTER_KEY"]
)

manager = CredentialManager(providers=[provider])
```

**Advantages:**
- Strong encryption (AES via Fernet)
- Persistent storage
- Secure file permissions (0600)
- Metadata tracking

**Disadvantages:**
- Requires cryptography library
- Master key management required
- Slower than environment variables

### Cloud Vaults (Future)

Support for HashiCorp Vault and AWS Secrets Manager is planned for future releases.

## Access Control

### Basic Access Control

```python
from lynguine.security import AccessPolicy, AccessLevel

policy = AccessPolicy()

# Allow specific user read access to production credentials
policy.add_rule(
    credential_pattern="prod_*",
    user_pattern="prod_user",
    access_level=AccessLevel.READ
)

# Allow admins full access to all credentials
policy.add_rule(
    credential_pattern="*",
    user_pattern="admin",
    access_level=AccessLevel.ADMIN
)
```

### Access Levels

- `NONE`: No access
- `READ`: Can retrieve credentials
- `WRITE`: Can create and update credentials
- `DELETE`: Can delete credentials
- `ADMIN`: Full access to all operations

### Authorization

```python
from lynguine.security import CredentialAccessController, AccessLevel

controller = CredentialAccessController()

# Authorize access before retrieving credentials
controller.authorize_access(
    credential_key="google_sheets_oauth",
    operation=AccessLevel.READ,
    user="current_user",
    context="data_processing"
)
```

## Audit Logging

### Enable Audit Logging

```python
from lynguine.security import AuditLogger, AuditEventType

# Create audit logger
audit_logger = AuditLogger(
    log_path="~/.lynguine/audit.log",
    enable_file=True,
    enable_console=False
)
```

### Query Audit Events

```python
from datetime import datetime, timedelta

# Query last 24 hours of credential access events
events = audit_logger.query_events(
    event_type=AuditEventType.CREDENTIAL_ACCESS,
    start_time=datetime.now() - timedelta(days=1),
    limit=100
)

for event in events:
    print(f"{event['timestamp']}: {event['user']} accessed {event['credential_key']}")
```

### Audit Event Types

- `CREDENTIAL_ACCESS`: Credential retrieved
- `CREDENTIAL_CREATE`: New credential created
- `CREDENTIAL_UPDATE`: Credential modified
- `CREDENTIAL_DELETE`: Credential deleted
- `ACCESS_DENIED`: Access attempt denied
- `VALIDATION_FAILED`: Credential validation failed
- `RATE_LIMIT_EXCEEDED`: Rate limit triggered

## Secure Logging

Prevent credential leakage in application logs:

```python
from lynguine.security import get_secure_logger, setup_secure_logging

# Get a secure logger that automatically sanitizes sensitive data
logger = get_secure_logger(__name__)

# Sensitive data is automatically redacted
logger.info(f"Connecting with api_key={api_key}")
# Output: "Connecting with api_key=***API_KEY***"

# Set up secure logging for the entire application
setup_secure_logging(level=logging.INFO)
```

### Custom Sanitization

```python
from lynguine.security import sanitize_dict

sensitive_data = {
    "username": "john",
    "password": "secret123",
    "api_key": "abc-xyz-123"
}

sanitized = sanitize_dict(sensitive_data)
print(sanitized)
# {'username': 'john', 'password': '***', 'api_key': '***REDACTED***'}
```

## Migration

### Automated Migration

Migrate existing plain-text credentials to secure storage:

```python
from lynguine.security import CredentialMigrator

# Set master key for encrypted storage
import os
os.environ["LYNGUINE_MASTER_KEY"] = "your-master-key"

# Create migrator
migrator = CredentialMigrator()

# Migrate Google Sheets credentials
report = migrator.migrate_google_sheets_credentials(
    config_file="~/.lynguine/config/machine.yml",
    credential_name="google_sheets_oauth",
    dry_run=False  # Set True to test first
)

print(f"Migrated: {len(report['migrated'])} credentials")
print(f"Errors: {len(report['errors'])} errors")

# Validate migration
validation = migrator.validate_migration("~/.lynguine/config/machine.yml")
if validation['valid']:
    print("✓ Migration successful")
else:
    print("✗ Issues found:", validation['issues'])
```

### Manual Migration Steps

1. **Backup Configuration**
   ```bash
   cp ~/.lynguine/config/machine.yml ~/.lynguine/config/machine.yml.backup
   ```

2. **Set Master Key**
   ```bash
   export LYNGUINE_MASTER_KEY="your-secure-master-password"
   ```

3. **Store Credentials**
   ```python
   from lynguine.security import set_credential
   
   set_credential("google_sheets_oauth", {
       "client_id": "your-client-id",
       "client_secret": "your-client-secret"
   })
   ```

4. **Update Configuration**
   
   Replace:
   ```yaml
   google_oauth:
     client_id: your-client-id
     client_secret: your-client-secret
   ```
   
   With:
   ```yaml
   google_oauth: ${credential:google_sheets_oauth}
   ```

5. **Test**
   ```python
   from lynguine import Interface
   
   interface = Interface.from_file("_lynguine.yml")
   # Should work without errors
   ```

### Rollback

If migration fails, restore from backup:

```python
migrator.rollback("/path/to/backup/machine.yml.backup_20231215_143022")
```

## Advanced Configuration

### Multiple Providers with Priority

```python
from lynguine.security import (
    CredentialManager,
    EnvironmentCredentialProvider,
    EncryptedFileCredentialProvider
)

# Environment variables take priority (e.g., for dev overrides)
env_provider = EnvironmentCredentialProvider(prefix="LYNGUINE_CRED")

# Encrypted files for production credentials
file_provider = EncryptedFileCredentialProvider(
    storage_path="~/.lynguine/credentials",
    master_key=os.environ["LYNGUINE_MASTER_KEY"]
)

# Create manager with priority order
manager = CredentialManager(
    providers=[env_provider, file_provider],  # env checked first
    cache_ttl=300,  # 5 minute cache
    enable_cache=True
)
```

### Custom Validators

```python
from lynguine.security import get_credential_manager

manager = get_credential_manager()

# Register custom validator
def validate_google_oauth(credential):
    """Ensure Google OAuth has required fields."""
    if "value" not in credential:
        return False
    value = credential["value"]
    required = ["client_id", "client_secret", "redirect_uri"]
    return all(field in value for field in required)

manager.register_validator("google_oauth", validate_google_oauth)

# Credentials are now validated on retrieval
creds = manager.get_credential("google_auth", credential_type="google_oauth")
```

### Rate Limiting

```python
from lynguine.security import RateLimiter

# Limit to 100 requests per minute per user
limiter = RateLimiter(max_requests=100, time_window=60)

if not limiter.check_rate_limit("google_sheets_oauth", user="current_user"):
    raise Exception("Rate limit exceeded")
```

## Security Best Practices

### 1. Master Key Management

**DO:**
- Generate strong master keys (20+ characters, mixed case, numbers, symbols)
- Store master key in secure key management system
- Use different master keys for dev/staging/production
- Rotate master key periodically

**DON'T:**
- Hard-code master key in source code
- Commit master key to version control
- Share master key via email or chat
- Use weak or predictable master keys

### 2. Credential Storage

**DO:**
- Use encrypted file storage for production
- Set restrictive file permissions (0600)
- Store credentials outside of application directory
- Back up encrypted credential files securely

**DON'T:**
- Store credentials in plain text
- Use world-readable permissions
- Store credentials in application repository
- Forget to backup credentials

### 3. Access Control

**DO:**
- Implement principle of least privilege
- Use specific credential patterns
- Monitor audit logs regularly
- Set up rate limiting

**DON'T:**
- Grant blanket admin access
- Ignore access denied events
- Disable audit logging
- Allow unlimited credential access

### 4. Credential Lifecycle

**DO:**
- Rotate credentials regularly (90 days or less)
- Revoke credentials immediately on compromise
- Track credential usage via audit logs
- Test credential rotation procedures

**DON'T:**
- Use the same credentials indefinitely
- Leave old credentials active after rotation
- Forget to update credential references
- Skip testing after rotation

## Troubleshooting

### Common Issues

#### "Credential not found" Error

```python
# Check available credentials
from lynguine.security import get_credential_manager

manager = get_credential_manager()
print("Available credentials:", manager.list_credentials())
```

#### "Access denied" Error

```python
# Check access policy
from lynguine.security import get_access_controller

controller = get_access_controller()
# Review and update policies as needed
```

#### "Cryptography library not available"

```bash
pip install cryptography
```

#### Wrong Master Key

If you get decryption errors:
1. Verify master key is correct
2. Check `LYNGUINE_MASTER_KEY` environment variable
3. Ensure same master key was used for encryption

#### Migration Validation Failures

```python
# Get detailed validation report
validation = migrator.validate_migration("config.yml")
print("Issues:", validation['issues'])

# Check each credential reference
for ref in validation['credential_references']:
    try:
        cred = manager.get_credential(ref)
        print(f"✓ {ref}: OK")
    except Exception as e:
        print(f"✗ {ref}: {e}")
```

## API Reference

### Core Functions

- `get_credential(key, credential_type=None, default=None)`: Retrieve a credential
- `set_credential(key, value, credential_type=None)`: Store a credential
- `get_credential_manager()`: Get global credential manager
- `get_access_controller()`: Get global access controller

### Classes

- `CredentialManager`: Central credential management
- `EnvironmentCredentialProvider`: Environment variable backend
- `EncryptedFileCredentialProvider`: Encrypted file backend
- `CredentialAccessController`: Access control and auditing
- `AuditLogger`: Security event logging
- `CredentialMigrator`: Migration utilities

See module documentation for detailed API reference.

## Examples

### Example 1: Simple Google Sheets Integration

```python
from lynguine.security import set_credential
from lynguine import Interface

# One-time setup: Store credentials
google_creds = {
    "client_id": "123456789.apps.googleusercontent.com",
    "client_secret": "your-client-secret",
    "redirect_uri": "http://localhost:8080"
}
set_credential("google_sheets_oauth", google_creds)

# Update _lynguine.yml:
# google_oauth: ${credential:google_sheets_oauth}

# Use normally
interface = Interface.from_file("_lynguine.yml")
data, _ = interface.read_inputs()
```

### Example 2: Multi-Environment Setup

```python
import os
from lynguine.security import (
    CredentialManager,
    EnvironmentCredentialProvider,
    EncryptedFileCredentialProvider
)

# Detect environment
env = os.environ.get("LYNGUINE_ENV", "development")

if env == "production":
    # Production: Use encrypted files only
    provider = EncryptedFileCredentialProvider(
        storage_path="/var/lynguine/credentials",
        master_key=os.environ["LYNGUINE_MASTER_KEY"]
    )
else:
    # Development: Use environment variables
    provider = EnvironmentCredentialProvider()

manager = CredentialManager(providers=[provider])
```

### Example 3: Credential Rotation

```python
from lynguine.security import get_credential_manager

manager = get_credential_manager()

# Store new credentials
new_creds = {
    "client_id": "new-client-id",
    "client_secret": "new-client-secret"
}

# Update with new credentials
manager.set_credential("google_sheets_oauth", new_creds)

# Invalidate cache to force refresh
if manager.cache:
    manager.cache.invalidate("google_sheets_oauth")

print("Credentials rotated successfully")
```

## Support and Resources

- [GitHub Issues](https://github.com/lawrennd/lynguine/issues)
- [Documentation](https://lynguine.readthedocs.io)
- [Security Policy](../SECURITY.md)
- [Contributing Guide](../CONTRIBUTING.md)

## License

This security module is part of Lynguine and is licensed under the same license as the main project.

