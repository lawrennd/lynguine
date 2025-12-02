"""
Migration tools for transitioning to secure credential management.

This module provides utilities to migrate existing credential configurations
to the new secure credential management system.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil
from datetime import datetime

from .credentials import (
    get_credential_manager,
    EnvironmentCredentialProvider,
    EncryptedFileCredentialProvider,
    CredentialError,
    CredentialManager,
    CRYPTO_AVAILABLE
)
from .secure_logging import get_secure_logger


logger = get_secure_logger(__name__)


class MigrationError(Exception):
    """Exception raised during migration."""
    pass


class CredentialMigrator:
    """
    Tool for migrating credentials to secure storage.
    
    This class helps migrate from:
    - Plain text configuration files
    - Environment variables (documentation only)
    - Legacy credential storage
    
    To the new secure credential management system.
    """
    
    def __init__(
        self,
        credential_manager: CredentialManager = None,
        backup_dir: str = None
    ):
        """
        Initialize the credential migrator.
        
        :param credential_manager: Credential manager to use (uses global if None)
        :type credential_manager: CredentialManager
        :param backup_dir: Directory for backups
        :type backup_dir: str
        """
        self.credential_manager = credential_manager or get_credential_manager()
        
        if backup_dir is None:
            backup_dir = os.path.join(
                os.path.expanduser("~"),
                ".lynguine",
                "migration_backups"
            )
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        logger.info(f"Initialized migrator with backup dir: {self.backup_dir}")
    
    def backup_file(self, file_path: str) -> str:
        """
        Create a backup of a file before migration.
        
        :param file_path: Path to file to backup
        :type file_path: str
        :return: Path to backup file
        :rtype: str
        """
        if not os.path.exists(file_path):
            raise MigrationError(f"File not found: {file_path}")
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_name = f"{filename}.backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        os.chmod(backup_path, 0o600)  # Secure permissions
        
        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)
    
    def migrate_yaml_config(
        self,
        config_file: str,
        credential_mappings: Dict[str, str],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Migrate credentials from a YAML configuration file.
        
        :param config_file: Path to YAML configuration file
        :type config_file: str
        :param credential_mappings: Map of config keys to credential names
        :type credential_mappings: Dict[str, str]
        :param dry_run: If True, don't make changes (default: False)
        :type dry_run: bool
        :return: Migration report
        :rtype: Dict[str, Any]
        """
        logger.info(f"Migrating credentials from: {config_file}")
        
        if not os.path.exists(config_file):
            raise MigrationError(f"Configuration file not found: {config_file}")
        
        # Backup original file
        if not dry_run:
            backup_path = self.backup_file(config_file)
        else:
            backup_path = None
        
        # Load configuration
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Track migration results
        migrated = []
        skipped = []
        errors = []
        
        # Process each credential mapping
        for config_key, credential_name in credential_mappings.items():
            try:
                # Extract credential value from config
                value = self._extract_nested_value(config, config_key)
                
                if value is None:
                    skipped.append({
                        "key": config_key,
                        "reason": "Not found in configuration"
                    })
                    continue
                
                # Store in secure credential management
                if not dry_run:
                    # Wrap value if it's not already a dict
                    if not isinstance(value, dict):
                        credential_value = {"value": value}
                    else:
                        credential_value = value
                    
                    self.credential_manager.set_credential(
                        credential_name,
                        credential_value
                    )
                
                # Replace with credential reference in config
                self._set_nested_value(
                    config,
                    config_key,
                    f"${{credential:{credential_name}}}"
                )
                
                migrated.append({
                    "config_key": config_key,
                    "credential_name": credential_name
                })
                
            except Exception as e:
                logger.error(f"Failed to migrate {config_key}: {e}")
                errors.append({
                    "key": config_key,
                    "error": str(e)
                })
        
        # Write updated configuration
        if not dry_run and migrated:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            os.chmod(config_file, 0o600)
        
        # Generate report
        report = {
            "config_file": config_file,
            "backup_path": backup_path,
            "dry_run": dry_run,
            "migrated": migrated,
            "skipped": skipped,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"Migration complete: {len(migrated)} migrated, "
            f"{len(skipped)} skipped, {len(errors)} errors"
        )
        
        return report
    
    def migrate_google_sheets_credentials(
        self,
        config_file: str,
        credential_name: str = "google_sheets_oauth",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Migrate Google Sheets credentials specifically.
        
        :param config_file: Path to configuration file
        :type config_file: str
        :param credential_name: Name for the credential in secure storage
        :type credential_name: str
        :param dry_run: If True, don't make changes
        :type dry_run: bool
        :return: Migration report
        :rtype: Dict[str, Any]
        """
        # Common Google Sheets credential keys
        mappings = {
            "google_oauth": credential_name,
            "gspread_pandas": f"{credential_name}_pandas"
        }
        
        return self.migrate_yaml_config(config_file, mappings, dry_run)
    
    def generate_environment_variable_script(
        self,
        credentials: Dict[str, Dict[str, Any]],
        output_file: str = None,
        shell: str = "bash"
    ) -> str:
        """
        Generate a shell script to set environment variables for credentials.
        
        :param credentials: Dictionary of credential_name -> credential_value
        :type credentials: Dict[str, Dict[str, Any]]
        :param output_file: Path to output script (optional)
        :type output_file: str
        :param shell: Shell type ("bash" or "fish")
        :type shell: str
        :return: Script content
        :rtype: str
        """
        lines = []
        
        if shell == "bash":
            lines.append("#!/bin/bash")
            lines.append("# Lynguine credential environment variables")
            lines.append("# Source this file to set credentials in your environment")
            lines.append("")
            
            for cred_name, cred_value in credentials.items():
                env_var = f"LYNGUINE_CRED_{cred_name.upper()}"
                # Convert to JSON for complex values
                if isinstance(cred_value, dict):
                    value_str = json.dumps(cred_value).replace('"', '\\"')
                else:
                    value_str = str(cred_value)
                lines.append(f'export {env_var}="{value_str}"')
        
        elif shell == "fish":
            lines.append("#!/usr/bin/env fish")
            lines.append("# Lynguine credential environment variables")
            lines.append("")
            
            for cred_name, cred_value in credentials.items():
                env_var = f"LYNGUINE_CRED_{cred_name.upper()}"
                if isinstance(cred_value, dict):
                    value_str = json.dumps(cred_value)
                else:
                    value_str = str(cred_value)
                lines.append(f'set -x {env_var} "{value_str}"')
        
        script = "\n".join(lines)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(script)
            os.chmod(output_file, 0o700)  # Make executable
            logger.info(f"Generated environment script: {output_file}")
        
        return script
    
    def _extract_nested_value(self, data: Dict, key_path: str) -> Any:
        """
        Extract a value from nested dictionary using dot notation.
        
        :param data: Dictionary to extract from
        :type data: Dict
        :param key_path: Key path (e.g., "parent.child.key")
        :type key_path: str
        :return: The value or None if not found
        """
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict, key_path: str, value: Any) -> None:
        """
        Set a value in nested dictionary using dot notation.
        
        :param data: Dictionary to modify
        :type data: Dict
        :param key_path: Key path (e.g., "parent.child.key")
        :type key_path: str
        :param value: Value to set
        """
        keys = key_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def validate_migration(self, config_file: str) -> Dict[str, Any]:
        """
        Validate that a migrated configuration works correctly.
        
        :param config_file: Path to configuration file
        :type config_file: str
        :return: Validation report
        :rtype: Dict[str, Any]
        """
        logger.info(f"Validating migration for: {config_file}")
        
        results = {
            "config_file": config_file,
            "valid": True,
            "credential_references": [],
            "issues": []
        }
        
        try:
            # Load configuration
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Find all credential references
            refs = self._find_credential_references(config)
            results["credential_references"] = refs
            
            # Validate each reference
            for ref in refs:
                try:
                    credential = self.credential_manager.get_credential(ref)
                    if credential is None:
                        results["issues"].append({
                            "reference": ref,
                            "error": "Credential not found in secure storage"
                        })
                        results["valid"] = False
                except CredentialError as e:
                    results["issues"].append({
                        "reference": ref,
                        "error": str(e)
                    })
                    results["valid"] = False
        
        except Exception as e:
            results["valid"] = False
            results["issues"].append({
                "error": f"Failed to validate configuration: {e}"
            })
        
        logger.info(
            f"Validation complete: {'PASS' if results['valid'] else 'FAIL'}"
        )
        return results
    
    def _find_credential_references(
        self,
        data: Any,
        refs: List[str] = None
    ) -> List[str]:
        """
        Recursively find all credential references in configuration.
        
        :param data: Data to search
        :param refs: List to accumulate references
        :type refs: List[str]
        :return: List of credential references
        :rtype: List[str]
        """
        if refs is None:
            refs = []
        
        if isinstance(data, str):
            # Look for ${credential:name} pattern
            import re
            pattern = r'\$\{credential:([^}]+)\}'
            matches = re.findall(pattern, data)
            refs.extend(matches)
        
        elif isinstance(data, dict):
            for value in data.values():
                self._find_credential_references(value, refs)
        
        elif isinstance(data, list):
            for item in data:
                self._find_credential_references(item, refs)
        
        return list(set(refs))  # Remove duplicates
    
    def rollback(self, backup_path: str) -> None:
        """
        Rollback a migration by restoring from backup.
        
        :param backup_path: Path to backup file
        :type backup_path: str
        """
        if not os.path.exists(backup_path):
            raise MigrationError(f"Backup file not found: {backup_path}")
        
        # Extract original filename
        backup_name = os.path.basename(backup_path)
        original_name = backup_name.split('.backup_')[0]
        
        # Determine original path (same directory as backup for safety)
        original_path = os.path.join(os.path.dirname(backup_path), original_name)
        
        # Restore
        shutil.copy2(backup_path, original_path)
        logger.info(f"Restored from backup: {original_path}")


def create_migration_guide() -> str:
    """
    Create a migration guide document.
    
    :return: Migration guide text
    :rtype: str
    """
    guide = """
# Lynguine Secure Credential Management Migration Guide

## Overview

This guide helps you migrate from plain-text credential storage to the new
secure credential management system in Lynguine.

## Prerequisites

1. Python 3.6 or higher
2. cryptography library (for encrypted storage):
   ```bash
   pip install cryptography
   ```

## Migration Steps

### Step 1: Backup Your Configuration

Before starting migration, backup your configuration files:

```bash
cp ~/.lynguine/config/machine.yml ~/.lynguine/config/machine.yml.backup
```

### Step 2: Set Master Key (for encrypted storage)

Set a master key for encrypting stored credentials:

```bash
export LYNGUINE_MASTER_KEY="your-secure-master-password"
```

**Important**: Store this master key securely! You'll need it to access encrypted credentials.

### Step 3: Run Migration

Use the migration tool to migrate your credentials:

```python
from lynguine.security.migration import CredentialMigrator

migrator = CredentialMigrator()

# Migrate Google Sheets credentials
report = migrator.migrate_google_sheets_credentials(
    config_file="~/.lynguine/config/machine.yml",
    dry_run=False  # Set to True to test first
)

print(f"Migrated: {len(report['migrated'])} credentials")
```

### Step 4: Validate Migration

Validate that the migration was successful:

```python
validation = migrator.validate_migration("~/.lynguine/config/machine.yml")
if validation['valid']:
    print("Migration successful!")
else:
    print("Issues found:", validation['issues'])
```

### Step 5: Update Your Code

Your existing code should continue to work without changes. The credential
management system provides backward compatibility.

## Credential Reference Syntax

After migration, your configuration will use credential references:

```yaml
google_oauth: ${credential:google_sheets_oauth}
```

## Environment Variable Alternative

If you prefer environment variables over encrypted files:

```bash
export LYNGUINE_CRED_GOOGLE_SHEETS_OAUTH='{"client_id":"...","client_secret":"..."}'
```

## Rollback

If you need to rollback:

```python
migrator.rollback("/path/to/backup/machine.yml.backup_20231215_143022")
```

## Security Best Practices

1. **Use encrypted file storage** for production credentials
2. **Set restrictive file permissions** (0600) on credential files
3. **Don't commit credentials** to version control
4. **Rotate credentials regularly**
5. **Use different credentials** for development and production
6. **Monitor audit logs** for suspicious access

## Troubleshooting

### "Credential not found" Error

Ensure the credential was migrated successfully:

```python
from lynguine.security.credentials import get_credential_manager
manager = get_credential_manager()
creds = manager.list_credentials()
print("Available credentials:", creds)
```

### "Access denied" Error

Check access control policies and rate limits:

```python
from lynguine.security.access_control import get_access_controller
controller = get_access_controller()
# Adjust policies as needed
```

## Support

For issues or questions, see the Lynguine documentation or file an issue on GitHub.
"""
    return guide


def save_migration_guide(output_file: str = None) -> str:
    """
    Save the migration guide to a file.
    
    :param output_file: Path to output file (optional)
    :type output_file: str
    :return: Path to saved file
    :rtype: str
    """
    if output_file is None:
        output_file = os.path.join(
            os.path.expanduser("~"),
            ".lynguine",
            "MIGRATION_GUIDE.md"
        )
    
    guide = create_migration_guide()
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(guide)
    
    logger.info(f"Migration guide saved to: {output_path}")
    return str(output_path)

