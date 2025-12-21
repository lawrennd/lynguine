# Lynguine Secure Credential Management - User Guide

**A practical guide to securing your API credentials and OAuth tokens**

> 💡 **New to Lynguine security?** Start with the [Quick Start](#quick-start-5-minutes) to get up and running in 5 minutes!

---

## Table of Contents

1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [Installation & Setup](#installation--setup)
3. [Basic Usage](#basic-usage)
   - [Environment Variables](#using-environment-variables)
   - [Encrypted Files](#using-encrypted-files)
   - [Getting Credentials](#getting-credentials-in-code)
4. [Common Scenarios](#common-scenarios)
   - [Google Sheets Setup](#scenario-1-google-sheets-credentials)
   - [CI/CD Integration](#scenario-2-cicd-pipelines)
   - [Production Deployment](#scenario-3-production-deployment)
5. [Migration Guide](#migration-guide)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)
9. [API Reference](#api-reference)

---

## Quick Start (5 Minutes)

Get secure credential management working in 5 minutes:

### Step 1: Set up a credential using environment variables

```bash
# Export your Google Sheets OAuth credentials
export LYNGUINE_CRED_GOOGLE_SHEETS='{"client_id":"your-id","client_secret":"your-secret","redirect_uri":"http://localhost:8080"}'
```

### Step 2: Update your Lynguine configuration

In your `_lynguine.yml` or project configuration:

```yaml
google_oauth: ${credential:GOOGLE_SHEETS}
```

### Step 3: Use Lynguine normally

```python
import lynguine as lyn

# Read from Google Sheets - credentials are handled securely!
data = lyn.access.io.read_gsheet({
    "filename": "MySpreadsheet",
    "sheet": "Sheet1",
    "header": 0
})
```

That's it! Your credentials are now managed securely. 🎉

**Want more?** Continue reading for production-grade encryption, access control, and best practices.

---

## Installation & Setup

### Basic Installation

Lynguine's secure credential management works out of the box with no additional dependencies for environment variable storage.

### Optional: Encrypted Storage

For production environments with encrypted file storage:

```bash
# Install cryptography library
pip install cryptography

# Or if using conda
conda install cryptography
```

### Verify Installation

```python
from lynguine.security import get_credential_manager

manager = get_credential_manager()
print(f"Credential manager ready with {len(manager.providers)} provider(s)")
```

---

## Basic Usage

### Using Environment Variables

**Best for**: Development, CI/CD, Docker containers

Environment variables provide the simplest way to store credentials:

#### Setting Credentials

```bash
# Format: LYNGUINE_CRED_<KEY_NAME>='<JSON_VALUE>'
export LYNGUINE_CRED_MY_API_KEY='{"api_key":"secret123","endpoint":"https://api.example.com"}'

# For simple strings, use JSON string format
export LYNGUINE_CRED_SIMPLE_TOKEN='"my-token-value"'
```

#### Using in Lynguine

```yaml
# In _lynguine.yml
my_api: ${credential:MY_API_KEY}
```

```python
# In Python code
from lynguine.security import get_credential

creds = get_credential("MY_API_KEY")
api_key = creds["value"]["api_key"]
```

#### Advantages

- ✅ No files or encryption setup needed
- ✅ Works great with Docker and CI/CD
- ✅ Easy to rotate credentials
- ✅ No dependencies required

#### Disadvantages

- ⚠️ Credentials visible in process environment
- ⚠️ Lost when process ends
- ⚠️ Not suitable for persistent storage

---

### Using Encrypted Files

**Best for**: Production, persistent storage, desktop applications

Encrypted files provide persistent, secure credential storage:

#### Initial Setup

```bash
# 1. Set a master key (store this securely - you'll need it!)
export LYNGUINE_MASTER_KEY="your-very-secure-master-password"

# 2. Credentials will be stored in ~/.lynguine/credentials/ by default
# The directory will be created automatically with secure permissions
```

#### Storing Credentials

```python
from lynguine.security import set_credential

# Store Google Sheets credentials
google_creds = {
    "client_id": "123456789-abc.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8080"
}

set_credential("google_sheets_oauth", google_creds)
print("✓ Credentials encrypted and stored!")
```

#### Using Encrypted Credentials

Once stored, use them like any other credentials:

```yaml
# In _lynguine.yml
google_oauth: ${credential:google_sheets_oauth}
```

Lynguine will automatically:
1. Find the encrypted credential file
2. Decrypt it using your master key
3. Use it securely

#### File Storage Location

```
~/.lynguine/credentials/
├── google_sheets_oauth.enc  # Encrypted credential file
├── my_api_key.enc
└── ...
```

Each file:
- Uses AES-256 encryption via Fernet
- Has 0600 permissions (only you can read)
- Contains encrypted credential + metadata

#### Advantages

- ✅ Strong encryption (AES-256)
- ✅ Persistent storage
- ✅ Automatic file permissions (0600)
- ✅ Credential versioning and metadata

#### Disadvantages

- ⚠️ Requires `cryptography` library
- ⚠️ Must manage master key securely
- ⚠️ Slower than environment variables

---

### Getting Credentials in Code

#### Simple Retrieval

```python
from lynguine.security import get_credential

# Get a credential
creds = get_credential("my_api_key")
print(creds["value"])  # The actual credential data
```

#### With Error Handling

```python
from lynguine.security import get_credential, CredentialNotFoundError

try:
    creds = get_credential("my_api_key")
    api_key = creds["value"]["api_key"]
except CredentialNotFoundError:
    print("Credential not found! Please set MY_API_KEY environment variable.")
    api_key = None
```

#### Type Validation

```python
from lynguine.security import get_credential_manager

manager = get_credential_manager()

# Validate credential matches expected type
creds = manager.get_credential(
    "google_sheets_oauth",
    credential_type="google_oauth"  # Validates structure
)
```

---

## Common Scenarios

### Scenario 1: Google Sheets Credentials

**Goal**: Securely access Google Sheets using OAuth credentials

#### Step 1: Get Your OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing one
3. Enable Google Sheets API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON

#### Step 2: Store Credentials Securely

**Option A: Environment Variables (Development)**

```bash
export LYNGUINE_CRED_GOOGLE_SHEETS='{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_SECRET","redirect_uri":"http://localhost:8080"}'
```

**Option B: Encrypted Files (Production)**

```python
from lynguine.security import set_credential

# Load from your downloaded credentials file
import json
with open("client_secret.json") as f:
    creds = json.load(f)["installed"]  # or ["web"] depending on type

set_credential("google_sheets_oauth", creds)
```

#### Step 3: Configure Lynguine

```yaml
# _lynguine.yml
google_oauth: ${credential:google_sheets_oauth}
```

Or use the legacy format (still supported):

```yaml
# _lynguine.yml
google_oauth:
  client_id: ${credential:google_sheets_oauth.client_id}
  client_secret: ${credential:google_sheets_oauth.client_secret}
  redirect_uri: ${credential:google_sheets_oauth.redirect_uri}
```

#### Step 4: Use Lynguine Normally

```python
import lynguine as lyn

# Read from Google Sheets
data = lyn.access.io.read_gsheet({
    "filename": "MySpreadsheet",
    "sheet": "Sheet1",
    "header": 0
})

# Write to Google Sheets
lyn.access.io.write_gsheet(data, {
    "filename": "MySpreadsheet",
    "sheet": "Output",
    "header": 0
})
```

---

### Scenario 2: CI/CD Pipelines

**Goal**: Use secure credentials in GitHub Actions, GitLab CI, or other CI/CD systems

#### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install lynguine
    
    - name: Set up credentials
      env:
        GOOGLE_SHEETS_CREDS: ${{ secrets.GOOGLE_SHEETS_CREDS }}
      run: |
        # GitHub secrets are automatically masked in logs
        export LYNGUINE_CRED_GOOGLE_SHEETS="$GOOGLE_SHEETS_CREDS"
    
    - name: Run tests
      env:
        LYNGUINE_CRED_GOOGLE_SHEETS: ${{ secrets.GOOGLE_SHEETS_CREDS }}
      run: |
        python -m pytest tests/
```

#### Setting Secrets in GitHub

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `GOOGLE_SHEETS_CREDS`
4. Value: `{"client_id":"...","client_secret":"...","redirect_uri":"..."}`
5. Click **Add secret**

#### GitLab CI Example

```yaml
# .gitlab-ci.yml
test:
  stage: test
  image: python:3.11
  
  variables:
    LYNGUINE_CRED_GOOGLE_SHEETS: $GOOGLE_SHEETS_CREDS
  
  before_script:
    - pip install lynguine
  
  script:
    - python -m pytest tests/
```

Set `GOOGLE_SHEETS_CREDS` in **Settings** → **CI/CD** → **Variables** (masked & protected)

---

### Scenario 3: Production Deployment

**Goal**: Deploy Lynguine application with encrypted credentials

#### Architecture

```
Production Server
├── Application Code
├── Environment Variables (LYNGUINE_MASTER_KEY only)
└── Encrypted Credentials (~/.lynguine/credentials/)
```

#### Step 1: Prepare Credentials Locally

```python
# setup_production_creds.py
from lynguine.security import set_credential, EncryptedFileCredentialProvider
import os

# Set production master key
os.environ["LYNGUINE_MASTER_KEY"] = "your-production-master-key"

# Create provider with custom path
provider = EncryptedFileCredentialProvider(
    storage_path="./production_credentials"
)

# Store all production credentials
set_credential("google_sheets_oauth", {
    "client_id": "prod-client-id",
    "client_secret": "prod-client-secret",
    "redirect_uri": "https://prod.example.com/oauth"
})

set_credential("api_key", {
    "key": "prod-api-key-123",
    "endpoint": "https://api.prod.example.com"
})

print("✓ Production credentials encrypted")
```

#### Step 2: Transfer Encrypted Files

```bash
# Copy encrypted files to production server (they're safe to transfer!)
scp -r production_credentials/ user@prod-server:~/.lynguine/credentials/
```

#### Step 3: Set Master Key on Production

```bash
# On production server - DO NOT commit this to git!
export LYNGUINE_MASTER_KEY="your-production-master-key"

# For systemd service, add to /etc/systemd/system/myapp.service:
[Service]
Environment="LYNGUINE_MASTER_KEY=your-production-master-key"
```

#### Step 4: Deploy Application

```python
# Your application code - no changes needed!
import lynguine as lyn

data = lyn.access.io.read_gsheet({
    "filename": "ProductionData",
    "sheet": "Sheet1"
})
```

#### Security Checklist for Production

- ✅ Master key stored in environment variable (not in code)
- ✅ Credential files have 0600 permissions
- ✅ Master key different from development
- ✅ Credentials rotated regularly
- ✅ Audit logging enabled
- ✅ Backup of encrypted credentials
- ❌ Never commit master key to git
- ❌ Never log or print credentials

---

## Migration Guide

### Migrating from `machine.yml` Plain-Text Credentials

If you currently store credentials in `machine.yml` like this:

```yaml
# machine.yml (OLD - insecure!)
google_oauth:
  client_id: "123456789-abc.apps.googleusercontent.com"
  client_secret: "YOUR_CLIENT_SECRET"
  redirect_uri: "http://localhost:8080"
```

Here's how to migrate to secure credential management:

#### Automatic Migration (Recommended)

```python
from lynguine.security.migration import CredentialMigrator
import os

# Set up master key for encrypted storage
os.environ["LYNGUINE_MASTER_KEY"] = "your-secure-master-password"

# Create migrator
migrator = CredentialMigrator()

# Preview changes (dry run)
migrator.migrate_yaml_config(
    config_file="machine.yml",
    dry_run=True
)

# Actually migrate (creates backup automatically)
migrator.migrate_yaml_config(
    config_file="machine.yml",
    backup=True
)

print("✓ Migration complete! Backup saved as machine.yml.backup")
```

The migrator will:
1. ✅ Create backup of original file
2. ✅ Extract all credentials
3. ✅ Store them encrypted
4. ✅ Update config file with credential references
5. ✅ Validate the migration

#### Manual Migration

**Step 1: Extract Credentials**

```python
from lynguine.security import set_credential
import yaml

# Load existing config
with open("machine.yml") as f:
    config = yaml.safe_load(f)

# Store Google OAuth creds securely
if "google_oauth" in config:
    set_credential("google_sheets_oauth", config["google_oauth"])
    print("✓ Google OAuth credentials migrated")

# Store other credentials...
```

**Step 2: Update Configuration File**

```yaml
# machine.yml (NEW - secure!)
google_oauth: ${credential:google_sheets_oauth}
```

**Step 3: Backup and Remove Old File**

```bash
# Backup original file
cp machine.yml machine.yml.backup

# IMPORTANT: Make sure new system works before deleting!
# Test your application first

# Once verified, securely delete old file
shred -u machine.yml.backup  # Linux
# Or manually delete on other systems
```

#### Rollback If Needed

If something goes wrong:

```bash
# Restore from backup
cp machine.yml.backup machine.yml

# Remove encrypted credentials if needed
rm -rf ~/.lynguine/credentials/
```

#### Migration Validation

```python
from lynguine.security.migration import CredentialMigrator

migrator = CredentialMigrator()

# Validate migrated credentials
results = migrator.validate_migration("machine.yml")

if results["valid"]:
    print("✓ Migration successful!")
else:
    print("✗ Issues found:")
    for issue in results["issues"]:
        print(f"  - {issue}")
```

---

## Advanced Features

### Role-Based Access Control (RBAC)

Control who can access which credentials:

```python
from lynguine.security import (
    get_access_controller,
    AccessPolicy,
    AccessLevel
)

# Get the access controller
controller = get_access_controller()

# Create a policy
policy = AccessPolicy()

# Allow developers read-only access to dev credentials
policy.add_rule(
    credential_pattern="dev_*",
    user_pattern="developer",
    access_level=AccessLevel.READ
)

# Allow admins full access to production credentials
policy.add_rule(
    credential_pattern="prod_*",
    user_pattern="admin",
    access_level=AccessLevel.ADMIN
)

# Set the policy
controller.set_policy(policy)

# Now authorize access
try:
    controller.authorize_access(
        credential_key="prod_database",
        operation=AccessLevel.READ,
        context="production_read",
        user="developer"  # This will fail - devs can't access prod
    )
except AccessDeniedError as e:
    print(f"Access denied: {e}")
```

### Audit Logging

Track all credential access for compliance:

```python
from lynguine.security import get_access_controller

controller = get_access_controller()

# Query audit logs
events = controller.audit_logger.query_events(
    start_time="2025-12-01",
    end_time="2025-12-21",
    event_types=["CREDENTIAL_ACCESS", "ACCESS_DENIED"]
)

for event in events:
    print(f"{event.timestamp}: {event.event_type} - {event.credential_key} by {event.user}")
```

### Credential Rotation

Regularly update credentials for security:

```python
from lynguine.security import get_credential, set_credential
import datetime

# Get current credential
old_creds = get_credential("api_key")

# Generate new credentials (your API-specific process)
new_creds = {
    "key": "new-api-key-456",
    "endpoint": old_creds["value"]["endpoint"],
    "rotated_at": datetime.datetime.now().isoformat()
}

# Store new credentials
set_credential("api_key", new_creds)

# Verify new credentials work
# ... test your application ...

# Audit trail is automatically logged
print("✓ Credentials rotated successfully")
```

### Custom Credential Provider

Create your own storage backend:

```python
from lynguine.security import CredentialProvider, CredentialManager
from typing import Optional, Dict, Any, List

class DatabaseCredentialProvider(CredentialProvider):
    """Store credentials in a database"""
    
    def __init__(self, db_connection):
        super().__init__(name="Database")
        self.db = db_connection
    
    def get_credential(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        # Query database for credential
        result = self.db.query("SELECT * FROM credentials WHERE key = ?", key)
        if result:
            return {"value": result["data"]}
        return None
    
    def set_credential(self, key: str, value: Dict[str, Any], **kwargs) -> None:
        # Store in database
        self.db.execute("INSERT OR REPLACE INTO credentials VALUES (?, ?)", 
                       key, value)
    
    def delete_credential(self, key: str, **kwargs) -> None:
        self.db.execute("DELETE FROM credentials WHERE key = ?", key)
    
    def list_credentials(self, **kwargs) -> List[str]:
        results = self.db.query("SELECT key FROM credentials")
        return [r["key"] for r in results]

# Use custom provider
db_provider = DatabaseCredentialProvider(my_db_connection)
manager = CredentialManager(providers=[db_provider])
```

---

## Troubleshooting

### Common Issues

#### Issue: "CredentialNotFoundError: Credential not found: XXXX"

**Cause**: Credential hasn't been set or environment variable is missing.

**Solutions**:

1. **Check if environment variable is set:**
   ```bash
   echo $LYNGUINE_CRED_XXXX
   ```

2. **List available credentials:**
   ```python
   from lynguine.security import get_credential_manager
   
   manager = get_credential_manager()
   credentials = manager.list_credentials()
   print(f"Available credentials: {credentials}")
   ```

3. **Set the credential:**
   ```bash
   export LYNGUINE_CRED_XXXX='{"key":"value"}'
   ```
   Or:
   ```python
   from lynguine.security import set_credential
   set_credential("XXXX", {"key": "value"})
   ```

---

#### Issue: "CredentialEncryptionError: Failed to decrypt credential"

**Cause**: Wrong master key or corrupted credential file.

**Solutions**:

1. **Verify master key:**
   ```bash
   echo $LYNGUINE_MASTER_KEY
   # Make sure this matches the key used to encrypt
   ```

2. **Check file permissions:**
   ```bash
   ls -la ~/.lynguine/credentials/
   # Should show -rw------- (0600)
   ```

3. **Re-encrypt credential:**
   ```bash
   # Delete corrupted file
   rm ~/.lynguine/credentials/credential_name.enc
   
   # Re-store credential
   python -c "from lynguine.security import set_credential; set_credential('credential_name', {...})"
   ```

---

#### Issue: "ModuleNotFoundError: No module named 'cryptography'"

**Cause**: Trying to use encrypted storage without cryptography library.

**Solution**:

```bash
pip install cryptography

# Or with conda
conda install cryptography
```

---

#### Issue: "AccessDeniedError: Access denied to credential: XXXX"

**Cause**: RBAC policy denies access.

**Solutions**:

1. **Check access policy:**
   ```python
   from lynguine.security import get_access_controller
   
   controller = get_access_controller()
   policy = controller.policy
   
   # Check rules
   for rule in policy.rules:
       print(f"Pattern: {rule.credential_pattern}, Level: {rule.access_level}")
   ```

2. **Update policy to allow access:**
   ```python
   from lynguine.security import AccessLevel
   
   policy.add_rule(
       credential_pattern="XXXX",
       user_pattern="*",  # Allow all users
       access_level=AccessLevel.READ
   )
   ```

---

#### Issue: "RateLimitError: Rate limit exceeded"

**Cause**: Too many credential access attempts in short time (brute force protection).

**Solution**:

1. **Wait for rate limit window to expire** (default: 60 seconds)

2. **Check for infinite loops in code:**
   ```python
   # Bad - rapid repeated access
   for i in range(1000):
       creds = get_credential("my_key")  # Rate limited!
   
   # Good - cache the credential
   creds = get_credential("my_key")
   for i in range(1000):
       use_credential(creds)  # Use cached credential
   ```

3. **Adjust rate limits** (if you control the system):
   ```python
   from lynguine.security import RateLimiter
   
   limiter = RateLimiter(
       max_requests=100,  # Increase limit
       time_window=60
   )
   ```

---

#### Issue: Credentials appear in logs

**Cause**: Not using secure logging features.

**Solution**:

Use the secure logger:

```python
from lynguine.security import SecureLogger

# Replace regular logger
logger = SecureLogger(__name__)

# Credentials are automatically sanitized
logger.info(f"Using credentials: {creds}")  # Credentials masked in output
```

---

### Debugging Tips

#### Enable Debug Logging

```python
import logging

# Enable debug logging for credential system
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("lynguine.security")
logger.setLevel(logging.DEBUG)

# Now you'll see detailed credential access logs
```

#### Check Credential Manager Status

```python
from lynguine.security import get_credential_manager

manager = get_credential_manager()

print(f"Providers: {[p.name for p in manager.providers]}")
print(f"Cache enabled: {manager.enable_cache}")
print(f"Available credentials: {manager.list_credentials()}")
```

#### Test Credential Access

```python
from lynguine.security import get_credential

try:
    creds = get_credential("test_key", use_cache=False)
    print(f"✓ Credential found: {list(creds.keys())}")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
```

---

## Security Best Practices

### ✅ DO

1. **Use encrypted storage for production**
   ```python
   # Production
   set_credential("prod_key", {...})  # Encrypted
   ```

2. **Rotate credentials regularly**
   - API keys: Every 90 days
   - OAuth tokens: When expired
   - Passwords: Every 180 days

3. **Use different credentials per environment**
   ```python
   # Development
   set_credential("dev_api_key", {...})
   
   # Production
   set_credential("prod_api_key", {...})
   ```

4. **Enable audit logging**
   ```python
   from lynguine.security import get_access_controller
   
   controller = get_access_controller()
   # Logs are automatically written to ~/.lynguine/audit.log
   ```

5. **Use RBAC for multi-user environments**
   ```python
   policy.add_rule(
       credential_pattern="sensitive_*",
       user_pattern="admin",
       access_level=AccessLevel.ADMIN
   )
   ```

6. **Keep master keys secure**
   - Store in password manager
   - Different per environment
   - Never commit to git
   - Use environment variables

7. **Validate credentials**
   ```python
   creds = manager.get_credential(
       "api_key",
       credential_type="api_key"  # Validates format
   )
   ```

### ❌ DON'T

1. **Don't commit credentials to git**
   ```bash
   # Add to .gitignore
   echo "machine.yml" >> .gitignore
   echo ".lynguine/" >> .gitignore
   echo "*.env" >> .gitignore
   ```

2. **Don't log credentials**
   ```python
   # Bad
   print(f"API Key: {api_key}")
   
   # Good
   from lynguine.security import SecureLogger
   logger = SecureLogger(__name__)
   logger.info("Using API key")  # Credentials masked
   ```

3. **Don't use same master key everywhere**
   ```bash
   # Bad
   export LYNGUINE_MASTER_KEY="password123"  # Same for all environments
   
   # Good
   # Dev: export LYNGUINE_MASTER_KEY="dev-secure-key-xyz"
   # Prod: export LYNGUINE_MASTER_KEY="prod-different-key-abc"
   ```

4. **Don't store master key in code**
   ```python
   # Bad
   master_key = "hardcoded-password"
   
   # Good
   import os
   master_key = os.environ["LYNGUINE_MASTER_KEY"]
   ```

5. **Don't share encrypted files without master key**
   - Encrypted files alone are useless without master key
   - Transfer them separately via different channels

6. **Don't disable security features in production**
   ```python
   # Bad - disabling cache in production
   manager = CredentialManager(enable_cache=False)  # Slow!
   ```

7. **Don't ignore CredentialNotFoundError**
   ```python
   # Bad - silent failure
   try:
       creds = get_credential("key")
   except:
       pass  # What happens now?
   
   # Good - proper handling
   try:
       creds = get_credential("key")
   except CredentialNotFoundError:
       logger.error("Missing required credential: key")
       raise
   ```

---

## API Reference

### Quick Reference

```python
# Core functions
from lynguine.security import (
    get_credential,           # Get a credential
    set_credential,           # Store a credential
    delete_credential,        # Remove a credential
    list_credentials,         # List all credentials
    get_credential_manager,   # Get manager instance
    get_access_controller,    # Get access controller
)

# Providers
from lynguine.security import (
    EnvironmentCredentialProvider,     # Environment variables
    EncryptedFileCredentialProvider,   # Encrypted files
)

# Access Control
from lynguine.security import (
    AccessLevel,              # Access level enum
    AccessPolicy,             # Access control policy
    RateLimiter,             # Rate limiting
)

# Exceptions
from lynguine.security import (
    CredentialError,              # Base exception
    CredentialNotFoundError,      # Credential missing
    CredentialValidationError,    # Invalid credential
    CredentialEncryptionError,    # Encryption failed
    AccessDeniedError,            # Access denied
    RateLimitError,              # Rate limit exceeded
)

# Logging
from lynguine.security import (
    SecureLogger,            # Secure logging
    SanitizingFormatter,     # Log sanitization
)

# Migration
from lynguine.security.migration import (
    CredentialMigrator,      # Migration tool
)
```

### Function Details

#### `get_credential(key, use_cache=True)`

Retrieve a credential by key.

**Parameters:**
- `key` (str): Credential key/identifier
- `use_cache` (bool): Whether to use cached value (default: True)

**Returns:**
- dict: Credential data with structure:
  ```python
  {
      "value": {...},      # The actual credential data
      "metadata": {...}    # Optional metadata
  }
  ```

**Raises:**
- `CredentialNotFoundError`: If credential doesn't exist

**Example:**
```python
creds = get_credential("google_sheets_oauth")
client_id = creds["value"]["client_id"]
```

---

#### `set_credential(key, value, provider_name=None)`

Store a credential.

**Parameters:**
- `key` (str): Credential key/identifier
- `value` (dict): Credential data to store
- `provider_name` (str, optional): Specific provider to use

**Example:**
```python
set_credential("my_api_key", {
    "key": "secret123",
    "endpoint": "https://api.example.com"
})
```

---

#### `delete_credential(key, provider_name=None)`

Remove a credential.

**Parameters:**
- `key` (str): Credential key/identifier
- `provider_name` (str, optional): Specific provider to use

**Example:**
```python
delete_credential("old_api_key")
```

---

#### `list_credentials(provider_name=None)`

List all available credential keys.

**Parameters:**
- `provider_name` (str, optional): List from specific provider only

**Returns:**
- list: List of credential keys

**Example:**
```python
keys = list_credentials()
print(f"Available credentials: {keys}")
```

---

### For More Details

- **Technical Implementation**: See `docs/security/IMPLEMENTATION_SUMMARY.md`
- **API Documentation**: See `docs/security/SECURE_CREDENTIALS.md`
- **CIP-0005**: See `cip/cip0005.md` for full design rationale

---

## Getting Help

- **Documentation**: Check this guide and related docs in `docs/security/`
- **Issues**: Report bugs on GitHub: https://github.com/lawrennd/lynguine/issues
- **Code**: Review source in `lynguine/security/`

---

## Related Documentation

- [CIP-0005: Secure Credential Management System](../../cip/cip0005.md) - Full technical design
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [SECURE_CREDENTIALS.md](SECURE_CREDENTIALS.md) - API documentation

---

**Last Updated**: December 21, 2025  
**Version**: 1.0  
**Related CIP**: CIP-0005

