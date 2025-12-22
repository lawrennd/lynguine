---
id: "2025-12-22_migrate-dotenv-credentials"
title: "Migrate .env File Credentials to Secure Credential Management"
status: "Proposed"
priority: "Medium"
created: "2025-12-22"
last_updated: "2025-12-22"
owner: "Neil Lawrence"
github_issue: ""
dependencies: "CIP-0005"
tags:
- backlog
- features
- security
- credentials
- migration
---

# Task: Migrate .env File Credentials to Secure Credential Management

## Description

Several existing projects use `.env` files to store credentials (OpenAI API keys, Google Sheets OAuth, etc.). These credentials need to be migrated to the new secure credential management system (CIP-0005) that provides:

- Encrypted storage at rest
- Access control and auditing
- Better integration with lynguine's credential reference system
- Rotation support

This task involves:
1. Identifying all projects using `.env` files for credentials
2. Migrating credentials from `.env` format to the secure credential system
3. Updating project configurations to use credential references
4. Testing that migrated credentials work correctly
5. Documenting the migration for future reference

## Acceptance Criteria

- [ ] Identify all projects/directories using `.env` files for credentials
- [ ] Create inventory of credentials to migrate (by type, not by value):
  - [ ] OpenAI API keys
  - [ ] Google Sheets OAuth credentials
  - [ ] Other API credentials
- [ ] Install cryptography library if not already available
- [ ] Set up master key for encrypted credential storage
- [ ] Migrate credentials using `CredentialMigrator` or manual process:
  - [ ] Preview migration with dry-run mode
  - [ ] Execute migration with backup
  - [ ] Validate migration success
- [ ] Update project configurations to use credential references:
  - [ ] Replace `.env` loading with `${credential:key}` references
  - [ ] Update any direct environment variable references
- [ ] Test all migrated credentials:
  - [ ] OpenAI API calls work
  - [ ] Google Sheets access works
  - [ ] Other integrations work
- [ ] Securely archive or delete old `.env` files:
  - [ ] Create encrypted backup if needed
  - [ ] Remove plaintext `.env` files
  - [ ] Update `.gitignore` to prevent future commits
- [ ] Document migration in project README or configuration docs

## Implementation Notes

### Migration Approach

Use the automatic migration tools provided in CIP-0005:

```python
from lynguine.security.migration import CredentialMigrator
from lynguine.security import set_credential
import os
from dotenv import load_dotenv

# Option 1: Manual migration from .env
load_dotenv('.env')

# Migrate OpenAI credentials
if 'OPENAI_API_KEY' in os.environ:
    set_credential('openai_api_key', {
        'api_key': os.environ['OPENAI_API_KEY'],
        'organization': os.environ.get('OPENAI_ORG_ID', ''),
    })

# Migrate Google Sheets credentials
if 'GOOGLE_CLIENT_ID' in os.environ:
    set_credential('google_sheets_oauth', {
        'client_id': os.environ['GOOGLE_CLIENT_ID'],
        'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8080'),
    })

# Option 2: If using YAML config
migrator = CredentialMigrator()
migrator.migrate_yaml_config('config.yml', backup=True)
```

### Configuration Updates

Update project configurations to use credential references:

**Before (.env approach):**
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ['OPENAI_API_KEY']
```

**After (secure credentials):**
```python
from lynguine.security import get_credential

creds = get_credential('openai_api_key')
api_key = creds['value']['api_key']
```

Or in YAML configuration:
```yaml
# Before
openai_api_key: ${OPENAI_API_KEY}

# After
openai_api_key: ${credential:openai_api_key}
```

### Security Considerations

1. **Master Key**: Set up unique master key for encrypted storage:
   ```bash
   export LYNGUINE_MASTER_KEY="project-specific-secure-password"
   ```

2. **Backup Strategy**: Create encrypted backup of credentials before deleting `.env` files:
   ```bash
   # Backup encrypted credentials directory
   tar -czf credentials-backup-$(date +%Y%m%d).tar.gz ~/.lynguine/credentials/
   ```

3. **Secure Deletion**: Use secure deletion for `.env` files:
   ```bash
   shred -u .env  # Linux
   rm -P .env     # macOS
   ```

4. **Access Control**: Consider setting up RBAC if multiple users access credentials

### Testing Checklist

- [ ] OpenAI API calls succeed with migrated credentials
- [ ] Google Sheets read/write operations work
- [ ] No plaintext credentials remain in code or config files
- [ ] Credential references resolve correctly in all environments
- [ ] Backup and restore process works correctly

## Related

- **CIP**: CIP-0005 (Secure Credential Management System)
- **Documentation**: 
  - `docs/security/USER_GUIDE.md` - Migration Guide (lines 492-612)
  - `docs/security/IMPLEMENTATION_SUMMARY.md`
- **Code Files**:
  - `lynguine/security/credentials.py`
  - `lynguine/security/migration.py`

## Progress Updates

### 2025-12-22

Task created. Multiple projects identified that use `.env` files for storing credentials (OpenAI, Google Sheets, etc.). Need to migrate to secure credential management system to improve security posture.

**Next Steps**:
1. Install cryptography library if needed
2. Set up master key for project
3. Inventory all credentials in `.env` files
4. Run migration tool with dry-run first
5. Execute migration and validate

