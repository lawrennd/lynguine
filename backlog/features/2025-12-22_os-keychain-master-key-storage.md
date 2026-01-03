---
category: features
created: '2025-12-22'
dependencies: CIP-0005
github_issue: ''
id: 2025-12-22_os-keychain-master-key-storage
last_updated: '2025-12-22'
owner: Neil Lawrence
priority: High
related_cips: []
status: Proposed
tags:
- backlog
- features
- security
- credentials
- cross-platform
title: Integrate OS-Level Keychain Storage for Master Key
---

# Task: Integrate OS-Level Keychain Storage for Master Key

## Description

Currently, the `LYNGUINE_MASTER_KEY` required for encrypted credential storage must be provided via environment variables or hardcoded parameters. This is suboptimal because:

1. **Environment variables** are lost when sessions end
2. **Manual setup** required for each terminal/IDE
3. **No OS-level security** - env vars can be read by any process
4. **Poor user experience** - users must manage passwords manually

This task adds support for storing and retrieving the master key from OS-level credential storage:

- **macOS**: Keychain Access
- **Linux**: Secret Service API (GNOME Keyring, KWallet, etc.)
- **Windows**: Credential Manager

### Benefits

- ✅ **Persistent Storage**: Master key persists across sessions
- ✅ **OS Security**: Leverages OS encryption and access control
- ✅ **User-Friendly**: No environment variables needed
- ✅ **Cross-Platform**: Works on all major operating systems
- ✅ **Backward Compatible**: Falls back to environment variables

### Implementation Approach

Use Python's `keyring` library which provides a unified interface to OS-level credential stores across all platforms.

## Acceptance Criteria

### Core Functionality

- [ ] Install and integrate `keyring` library as an optional dependency
- [ ] Implement master key retrieval from OS keychain with fallback chain:
  1. Check OS keychain first
  2. Fall back to `LYNGUINE_MASTER_KEY` environment variable
  3. Fall back to direct parameter (existing behavior)
- [ ] Implement master key storage to OS keychain
- [ ] Add command-line utility to set/get/delete master key from keychain
- [ ] Update `EncryptedFileCredentialProvider` to use keychain by default

### Platform Support

- [ ] **macOS**: Integrate with Keychain Access
  - [ ] Store master key in login keychain
  - [ ] Use appropriate service name and account identifier
  - [ ] Test on macOS (available for testing)
- [ ] **Linux**: Integrate with Secret Service API
  - [ ] Support GNOME Keyring
  - [ ] Support KWallet
  - [ ] Test on Linux with available secret services
- [ ] **Windows**: Integrate with Credential Manager
  - [ ] Store in Windows Credential Manager
  - [ ] Use appropriate credential naming
  - [ ] Build to work on Windows (even without test machine)
  - [ ] Add CI/CD testing on Windows if possible

### Configuration & Options

- [ ] Add configuration option to enable/disable keychain storage
- [ ] Add configuration option to specify keychain service name
- [ ] Support multiple named master keys (e.g., "dev", "prod")
- [ ] Add option to migrate from environment variable to keychain
- [ ] Provide clear error messages when keychain is unavailable

### Testing Requirements

- [ ] **Unit Tests** (all platforms where possible):
  - [ ] Test keychain storage and retrieval
  - [ ] Test fallback to environment variable
  - [ ] Test fallback chain order
  - [ ] Test error handling when keychain unavailable
  - [ ] Test mock keychain for platforms not available
- [ ] **Integration Tests**:
  - [ ] Test end-to-end credential encryption/decryption with keychain master key
  - [ ] Test migration from env var to keychain
  - [ ] Test multiple master keys (dev/prod scenarios)
- [ ] **Platform-Specific Tests**:
  - [ ] macOS: Test Keychain Access integration
  - [ ] Linux: Test Secret Service with mock backend
  - [ ] Windows: Test Credential Manager with mock backend
- [ ] **CI/CD Testing**:
  - [ ] Add GitHub Actions workflow for Windows testing
  - [ ] Add GitHub Actions workflow for Linux testing
  - [ ] Add GitHub Actions workflow for macOS testing
  - [ ] Use mock keyring backends where OS keychain unavailable
- [ ] **Error Case Tests**:
  - [ ] Test when keyring library not installed
  - [ ] Test when OS keychain is locked/unavailable
  - [ ] Test when permission denied to keychain
  - [ ] Test invalid master key format

### Documentation

- [ ] Update `docs/security/USER_GUIDE.md` with keychain usage instructions
- [ ] Add platform-specific setup guides for each OS
- [ ] Document CLI utility usage
- [ ] Update `docs/security/IMPLEMENTATION_SUMMARY.md`
- [ ] Add troubleshooting section for keychain issues
- [ ] Document fallback behavior clearly

### Security Considerations

- [ ] Ensure keychain access is properly authenticated
- [ ] Use appropriate keychain service naming conventions
- [ ] Document security implications of keychain storage
- [ ] Add audit logging for keychain access
- [ ] Ensure master key is not logged or printed

## Implementation Notes

### Dependencies

Add to `setup.py` or `requirements.txt`:

```python
# Optional dependency for OS keychain integration
extras_require={
    'keychain': ['keyring>=23.0.0'],
}
```

### Key Retrieval Implementation

```python
# lynguine/security/credentials.py

import os
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

class EncryptedFileCredentialProvider(CredentialProvider):
    def __init__(
        self,
        storage_path: str = None,
        master_key: str = None,
        use_keychain: bool = True,
        keychain_service: str = "lynguine",
        keychain_account: str = "master_key",
        name: str = None
    ):
        """
        Initialize the encrypted file credential provider.
        
        :param use_keychain: Try to retrieve master key from OS keychain
        :param keychain_service: Service name for keychain storage
        :param keychain_account: Account name for keychain storage
        """
        super().__init__(name)
        
        if not CRYPTO_AVAILABLE:
            raise CredentialEncryptionError(
                "Cryptography library not available. "
                "Install with: pip install cryptography"
            )
        
        # Set storage path
        if storage_path is None:
            storage_path = os.path.join(
                os.path.expanduser("~"),
                ".lynguine",
                "credentials"
            )
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Retrieve master key with fallback chain
        self.master_key = self._get_master_key(
            master_key, 
            use_keychain, 
            keychain_service, 
            keychain_account
        )
        
        if not self.master_key:
            raise CredentialEncryptionError(
                "Master key required for encrypted file storage. "
                "Set master key in OS keychain, set LYNGUINE_MASTER_KEY environment "
                "variable, or pass master_key parameter."
            )
        
        self._fernet = None
        self._lock = threading.Lock()
        self.logger.debug(f"Initialized with storage path: {self.storage_path}")
    
    def _get_master_key(
        self, 
        direct_key: str = None,
        use_keychain: bool = True,
        service: str = "lynguine",
        account: str = "master_key"
    ) -> str:
        """
        Retrieve master key with fallback chain.
        
        Priority order:
        1. Direct parameter (if provided)
        2. OS keychain (if available and enabled)
        3. Environment variable
        
        :return: Master key or None if not found
        """
        # 1. Direct parameter (highest priority for backward compatibility)
        if direct_key:
            self.logger.debug("Using directly provided master key")
            return direct_key
        
        # 2. Try OS keychain
        if use_keychain and KEYRING_AVAILABLE:
            try:
                key = keyring.get_password(service, account)
                if key:
                    self.logger.info(f"Retrieved master key from OS keychain")
                    return key
                else:
                    self.logger.debug(
                        f"No master key found in OS keychain "
                        f"(service={service}, account={account})"
                    )
            except Exception as e:
                self.logger.warning(
                    f"Failed to retrieve master key from OS keychain: {e}"
                )
        elif use_keychain and not KEYRING_AVAILABLE:
            self.logger.debug(
                "OS keychain requested but keyring library not available. "
                "Install with: pip install keyring"
            )
        
        # 3. Environment variable (fallback)
        env_key = os.environ.get("LYNGUINE_MASTER_KEY")
        if env_key:
            self.logger.debug("Using master key from environment variable")
            return env_key
        
        # Not found anywhere
        return None
```

### CLI Utility for Master Key Management

```python
# lynguine/security/keychain_cli.py

import sys
import getpass
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

def set_master_key(service: str = "lynguine", account: str = "master_key"):
    """Interactively set the master key in OS keychain."""
    if not KEYRING_AVAILABLE:
        print("Error: keyring library not installed")
        print("Install with: pip install keyring")
        sys.exit(1)
    
    print(f"Setting master key for Lynguine")
    print(f"Service: {service}")
    print(f"Account: {account}")
    print()
    
    # Prompt for master key
    master_key = getpass.getpass("Enter master key: ")
    confirm = getpass.getpass("Confirm master key: ")
    
    if master_key != confirm:
        print("Error: Master keys do not match")
        sys.exit(1)
    
    # Store in keychain
    try:
        keyring.set_password(service, account, master_key)
        print(f"✓ Master key stored in OS keychain")
    except Exception as e:
        print(f"✗ Failed to store master key: {e}")
        sys.exit(1)

def get_master_key(service: str = "lynguine", account: str = "master_key"):
    """Retrieve the master key from OS keychain."""
    if not KEYRING_AVAILABLE:
        print("Error: keyring library not installed")
        sys.exit(1)
    
    try:
        key = keyring.get_password(service, account)
        if key:
            print(f"✓ Master key found in OS keychain")
            print(f"(Key not displayed for security)")
        else:
            print(f"✗ No master key found in OS keychain")
            print(f"Set one with: python -m lynguine.security.keychain_cli set")
    except Exception as e:
        print(f"✗ Failed to retrieve master key: {e}")
        sys.exit(1)

def delete_master_key(service: str = "lynguine", account: str = "master_key"):
    """Delete the master key from OS keychain."""
    if not KEYRING_AVAILABLE:
        print("Error: keyring library not installed")
        sys.exit(1)
    
    confirm = input(f"Delete master key from keychain? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled")
        return
    
    try:
        keyring.delete_password(service, account)
        print(f"✓ Master key deleted from OS keychain")
    except Exception as e:
        print(f"✗ Failed to delete master key: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m lynguine.security.keychain_cli {set|get|delete}")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "set":
        set_master_key()
    elif command == "get":
        get_master_key()
    elif command == "delete":
        delete_master_key()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: set, get, delete")
        sys.exit(1)
```

### Testing Strategy

#### Mock Keyring for Tests

```python
# tests/test_keychain_integration.py

import pytest
from unittest.mock import patch, MagicMock

class MockKeyring:
    """Mock keyring backend for testing."""
    
    def __init__(self):
        self.storage = {}
    
    def get_password(self, service, account):
        return self.storage.get((service, account))
    
    def set_password(self, service, account, password):
        self.storage[(service, account)] = password
    
    def delete_password(self, service, account):
        if (service, account) in self.storage:
            del self.storage[(service, account)]

@pytest.fixture
def mock_keyring():
    """Provide a mock keyring for tests."""
    return MockKeyring()

def test_master_key_from_keychain(mock_keyring):
    """Test retrieving master key from OS keychain."""
    with patch('lynguine.security.credentials.keyring', mock_keyring):
        # Store master key in mock keychain
        mock_keyring.set_password("lynguine", "master_key", "test-password")
        
        # Create provider - should retrieve from keychain
        provider = EncryptedFileCredentialProvider()
        
        assert provider.master_key == "test-password"

def test_fallback_to_environment_variable(mock_keyring, monkeypatch):
    """Test fallback to environment variable when keychain empty."""
    with patch('lynguine.security.credentials.keyring', mock_keyring):
        monkeypatch.setenv("LYNGUINE_MASTER_KEY", "env-password")
        
        # Create provider - should fall back to env var
        provider = EncryptedFileCredentialProvider()
        
        assert provider.master_key == "env-password"

def test_keychain_not_available():
    """Test graceful handling when keyring library not available."""
    with patch('lynguine.security.credentials.KEYRING_AVAILABLE', False):
        # Should fall back to environment variable
        # Test implementation...
        pass

@pytest.mark.skipif(not sys.platform.startswith('darwin'), reason="macOS only")
def test_macos_keychain_integration():
    """Integration test for macOS Keychain Access."""
    # Real keychain test on macOS
    pass

@pytest.mark.skipif(not sys.platform.startswith('linux'), reason="Linux only")
def test_linux_secret_service_integration():
    """Integration test for Linux Secret Service."""
    # Real secret service test on Linux
    pass

@pytest.mark.skipif(not sys.platform.startswith('win'), reason="Windows only")
def test_windows_credential_manager_integration():
    """Integration test for Windows Credential Manager."""
    # Real credential manager test on Windows
    pass
```

#### CI/CD Configuration

```yaml
# .github/workflows/test-keychain.yml
name: Keychain Integration Tests

on: [push, pull_request]

jobs:
  test-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -e .[keychain,test]
      - run: pytest tests/test_keychain_integration.py -k macos

  test-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -e .[keychain,test]
      - run: pytest tests/test_keychain_integration.py -k linux

  test-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -e .[keychain,test]
      - run: pytest tests/test_keychain_integration.py -k windows
```

### Migration Tool

Provide utility to migrate from environment variable to keychain:

```python
from lynguine.security import set_master_key_in_keychain
import os

# Migrate existing env var to keychain
if 'LYNGUINE_MASTER_KEY' in os.environ:
    master_key = os.environ['LYNGUINE_MASTER_KEY']
    set_master_key_in_keychain(master_key)
    print("✓ Master key migrated to OS keychain")
    print("You can now remove LYNGUINE_MASTER_KEY from your environment")
```

## Related

- **CIP**: CIP-0005 (Secure Credential Management System)
- **Future Enhancements**: Mentioned in CIP-0005 (lines 446-449) but for cloud vaults, not OS keychains
- **Documentation**: 
  - `docs/security/USER_GUIDE.md` (needs update)
  - `docs/security/IMPLEMENTATION_SUMMARY.md`
- **Code Files**:
  - `lynguine/security/credentials.py` (main changes)
  - New: `lynguine/security/keychain_cli.py`
  - Tests: `tests/test_keychain_integration.py`

## Security Considerations

1. **Keychain Authentication**: OS keychain access may require user authentication (password, biometric)
2. **Service Naming**: Use consistent service names ("lynguine") to avoid conflicts
3. **Backward Compatibility**: Must not break existing environment variable usage
4. **Audit Logging**: Log keychain access attempts for security monitoring
5. **Error Messages**: Be careful not to leak sensitive information in errors

## Progress Updates

### 2025-12-22

Task created. Current credential system requires `LYNGUINE_MASTER_KEY` in environment variables, which is not persistent or user-friendly. This enhancement will integrate with OS-level credential stores across macOS, Linux, and Windows.

**Key Requirements**:
- Cross-platform support (macOS Keychain, Linux Secret Service, Windows Credential Manager)
- Comprehensive testing including CI/CD on all platforms
- Build to work on Windows even without local Windows testing
- Backward compatible with existing environment variable approach
- CLI utility for easy master key management

**Next Steps**:
1. Research `keyring` library API and platform capabilities
2. Design fallback chain architecture
3. Implement core keychain integration
4. Add comprehensive tests with mocks for all platforms
5. Set up CI/CD testing on Windows/Linux/macOS
6. Update documentation with platform-specific guides