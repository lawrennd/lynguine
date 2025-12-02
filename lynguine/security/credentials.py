"""
Secure credential management for Lynguine.

This module provides secure credential storage, retrieval, and management
with support for multiple backends including environment variables, encrypted
files, and cloud vaults.
"""

import os
import abc
import json
import base64
import hashlib
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Optional dependencies for encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class CredentialError(Exception):
    """Base exception for credential-related errors."""
    pass


class CredentialNotFoundError(CredentialError):
    """Raised when a credential cannot be found."""
    pass


class CredentialValidationError(CredentialError):
    """Raised when credential validation fails."""
    pass


class CredentialEncryptionError(CredentialError):
    """Raised when credential encryption/decryption fails."""
    pass


class CredentialProvider(abc.ABC):
    """
    Abstract base class for credential providers.
    
    Credential providers implement different backends for storing and
    retrieving credentials securely.
    """
    
    def __init__(self, name: str = None):
        """
        Initialize the credential provider.
        
        :param name: Optional name for this provider instance
        :type name: str
        """
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abc.abstractmethod
    def get_credential(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieve a credential by key.
        
        :param key: The credential key/identifier
        :type key: str
        :param kwargs: Additional provider-specific parameters
        :return: The credential data or None if not found
        :rtype: Optional[Dict[str, Any]]
        :raises CredentialError: If credential retrieval fails
        """
        pass
    
    @abc.abstractmethod
    def set_credential(self, key: str, value: Dict[str, Any], **kwargs) -> None:
        """
        Store a credential.
        
        :param key: The credential key/identifier
        :type key: str
        :param value: The credential data to store
        :type value: Dict[str, Any]
        :param kwargs: Additional provider-specific parameters
        :raises CredentialError: If credential storage fails
        """
        pass
    
    @abc.abstractmethod
    def delete_credential(self, key: str, **kwargs) -> None:
        """
        Delete a credential.
        
        :param key: The credential key/identifier
        :type key: str
        :param kwargs: Additional provider-specific parameters
        :raises CredentialError: If credential deletion fails
        """
        pass
    
    @abc.abstractmethod
    def list_credentials(self, **kwargs) -> List[str]:
        """
        List available credential keys.
        
        :param kwargs: Additional provider-specific parameters
        :return: List of credential keys
        :rtype: List[str]
        :raises CredentialError: If listing fails
        """
        pass
    
    def validate_credential(self, key: str, value: Dict[str, Any]) -> bool:
        """
        Validate a credential's format and content.
        
        :param key: The credential key/identifier
        :type key: str
        :param value: The credential data to validate
        :type value: Dict[str, Any]
        :return: True if valid, False otherwise
        :rtype: bool
        """
        # Basic validation - can be overridden by subclasses
        if not isinstance(value, dict):
            return False
        if not key or not isinstance(key, str):
            return False
        return True


class EnvironmentCredentialProvider(CredentialProvider):
    """
    Credential provider that retrieves credentials from environment variables.
    
    This provider supports:
    - Direct environment variable lookup
    - Prefix-based variable naming (e.g., LYNGUINE_CRED_<KEY>)
    - JSON-encoded credential values
    - Validation of environment variable names
    """
    
    def __init__(self, prefix: str = "LYNGUINE_CRED", name: str = None):
        """
        Initialize the environment credential provider.
        
        :param prefix: Prefix for environment variable names
        :type prefix: str
        :param name: Optional name for this provider instance
        :type name: str
        """
        super().__init__(name)
        self.prefix = prefix
        self.logger.debug(f"Initialized with prefix: {prefix}")
    
    def _get_env_key(self, key: str) -> str:
        """
        Convert a credential key to an environment variable name.
        
        :param key: The credential key
        :type key: str
        :return: The environment variable name
        :rtype: str
        """
        # Sanitize key and convert to uppercase
        safe_key = key.upper().replace("-", "_").replace(".", "_")
        return f"{self.prefix}_{safe_key}"
    
    def get_credential(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieve a credential from environment variables.
        
        :param key: The credential key/identifier
        :type key: str
        :return: The credential data or None if not found
        :rtype: Optional[Dict[str, Any]]
        """
        env_key = self._get_env_key(key)
        value = os.environ.get(env_key)
        
        if value is None:
            # Try without prefix as fallback
            value = os.environ.get(key)
        
        if value is None:
            self.logger.debug(f"Credential not found: {key}")
            return None
        
        # Try to parse as JSON, fallback to string value
        try:
            credential = json.loads(value)
            if not isinstance(credential, dict):
                credential = {"value": credential}
        except (json.JSONDecodeError, TypeError):
            credential = {"value": value}
        
        self.logger.debug(f"Retrieved credential: {key}")
        return credential
    
    def set_credential(self, key: str, value: Dict[str, Any], **kwargs) -> None:
        """
        Store a credential in environment variables (current process only).
        
        Note: This only affects the current process and is not persistent.
        
        :param key: The credential key/identifier
        :type key: str
        :param value: The credential data to store
        :type value: Dict[str, Any]
        """
        if not self.validate_credential(key, value):
            raise CredentialValidationError(f"Invalid credential format for key: {key}")
        
        env_key = self._get_env_key(key)
        os.environ[env_key] = json.dumps(value)
        self.logger.info(f"Stored credential in environment: {key}")
    
    def delete_credential(self, key: str, **kwargs) -> None:
        """
        Delete a credential from environment variables (current process only).
        
        :param key: The credential key/identifier
        :type key: str
        """
        env_key = self._get_env_key(key)
        if env_key in os.environ:
            del os.environ[env_key]
            self.logger.info(f"Deleted credential from environment: {key}")
    
    def list_credentials(self, **kwargs) -> List[str]:
        """
        List available credentials in environment variables.
        
        :return: List of credential keys
        :rtype: List[str]
        """
        prefix_len = len(self.prefix) + 1  # +1 for underscore
        keys = []
        for env_key in os.environ.keys():
            if env_key.startswith(f"{self.prefix}_"):
                # Extract the original key
                key = env_key[prefix_len:].lower().replace("_", "-")
                keys.append(key)
        return keys


class EncryptedFileCredentialProvider(CredentialProvider):
    """
    Credential provider that stores encrypted credentials in files.
    
    This provider uses Fernet (symmetric encryption) with a key derived
    from a master password using PBKDF2.
    """
    
    def __init__(
        self,
        storage_path: str = None,
        master_key: str = None,
        name: str = None
    ):
        """
        Initialize the encrypted file credential provider.
        
        :param storage_path: Path to store encrypted credential files
        :type storage_path: str
        :param master_key: Master key/password for encryption
        :type master_key: str
        :param name: Optional name for this provider instance
        :type name: str
        :raises CredentialEncryptionError: If cryptography is not available
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
        
        # Set up encryption
        self.master_key = master_key or os.environ.get("LYNGUINE_MASTER_KEY")
        if not self.master_key:
            raise CredentialEncryptionError(
                "Master key required for encrypted file storage. "
                "Set LYNGUINE_MASTER_KEY environment variable or pass master_key parameter."
            )
        
        self._fernet = None
        self._lock = threading.Lock()
        self.logger.debug(f"Initialized with storage path: {self.storage_path}")
    
    def _get_fernet(self) -> 'Fernet':
        """
        Get or create Fernet cipher instance.
        
        :return: Fernet cipher instance
        :rtype: Fernet
        """
        if self._fernet is None:
            with self._lock:
                if self._fernet is None:
                    # Derive key from master password
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=b"lynguine-salt-v1",  # In production, use random salt
                        iterations=100000,
                        backend=default_backend()
                    )
                    key = base64.urlsafe_b64encode(
                        kdf.derive(self.master_key.encode())
                    )
                    self._fernet = Fernet(key)
        return self._fernet
    
    def _get_credential_path(self, key: str) -> Path:
        """
        Get the file path for a credential key.
        
        :param key: The credential key
        :type key: str
        :return: Path to credential file
        :rtype: Path
        """
        # Hash the key to create a safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.storage_path / f"{key_hash}.cred"
    
    def get_credential(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt a credential from file.
        
        :param key: The credential key/identifier
        :type key: str
        :return: The credential data or None if not found
        :rtype: Optional[Dict[str, Any]]
        """
        cred_path = self._get_credential_path(key)
        
        if not cred_path.exists():
            self.logger.debug(f"Credential file not found: {key}")
            return None
        
        try:
            with open(cred_path, "rb") as f:
                encrypted_data = f.read()
            
            fernet = self._get_fernet()
            decrypted_data = fernet.decrypt(encrypted_data)
            credential = json.loads(decrypted_data.decode())
            
            self.logger.debug(f"Retrieved and decrypted credential: {key}")
            return credential
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential {key}: {e}")
            raise CredentialEncryptionError(f"Failed to decrypt credential: {key}") from e
    
    def set_credential(self, key: str, value: Dict[str, Any], **kwargs) -> None:
        """
        Encrypt and store a credential to file.
        
        :param key: The credential key/identifier
        :type key: str
        :param value: The credential data to store
        :type value: Dict[str, Any]
        """
        if not self.validate_credential(key, value):
            raise CredentialValidationError(f"Invalid credential format for key: {key}")
        
        cred_path = self._get_credential_path(key)
        
        try:
            # Add metadata
            credential_data = {
                "key": key,
                "value": value,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Encrypt
            fernet = self._get_fernet()
            plaintext = json.dumps(credential_data).encode()
            encrypted_data = fernet.encrypt(plaintext)
            
            # Write with secure permissions
            with open(cred_path, "wb") as f:
                f.write(encrypted_data)
            os.chmod(cred_path, 0o600)
            
            self.logger.info(f"Stored encrypted credential: {key}")
        except Exception as e:
            self.logger.error(f"Failed to store credential {key}: {e}")
            raise CredentialEncryptionError(f"Failed to encrypt credential: {key}") from e
    
    def delete_credential(self, key: str, **kwargs) -> None:
        """
        Delete a credential file.
        
        :param key: The credential key/identifier
        :type key: str
        """
        cred_path = self._get_credential_path(key)
        if cred_path.exists():
            cred_path.unlink()
            self.logger.info(f"Deleted credential file: {key}")
    
    def list_credentials(self, **kwargs) -> List[str]:
        """
        List available credentials (by decrypting and reading metadata).
        
        Note: This requires decrypting all credential files.
        
        :return: List of credential keys
        :rtype: List[str]
        """
        keys = []
        for cred_file in self.storage_path.glob("*.cred"):
            try:
                with open(cred_file, "rb") as f:
                    encrypted_data = f.read()
                fernet = self._get_fernet()
                decrypted_data = fernet.decrypt(encrypted_data)
                credential = json.loads(decrypted_data.decode())
                if "key" in credential:
                    keys.append(credential["key"])
            except Exception as e:
                self.logger.warning(f"Failed to read credential file {cred_file}: {e}")
        return keys


class CredentialCache:
    """
    Thread-safe cache for credentials with TTL support.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize the credential cache.
        
        :param default_ttl: Default time-to-live in seconds
        :type default_ttl: int
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(f"{__name__}.CredentialCache")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a credential from cache if not expired.
        
        :param key: The credential key
        :type key: str
        :return: The cached credential or None
        :rtype: Optional[Dict[str, Any]]
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.utcnow() < entry["expires_at"]:
                    self.logger.debug(f"Cache hit: {key}")
                    return entry["value"]
                else:
                    # Expired, remove from cache
                    del self._cache[key]
                    self.logger.debug(f"Cache expired: {key}")
        return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> None:
        """
        Store a credential in cache with TTL.
        
        :param key: The credential key
        :type key: str
        :param value: The credential value
        :type value: Dict[str, Any]
        :param ttl: Time-to-live in seconds (optional)
        :type ttl: int
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at
            }
            self.logger.debug(f"Cached credential: {key} (TTL: {ttl}s)")
    
    def invalidate(self, key: str) -> None:
        """
        Remove a credential from cache.
        
        :param key: The credential key
        :type key: str
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.logger.debug(f"Invalidated cache: {key}")
    
    def clear(self) -> None:
        """Clear all cached credentials."""
        with self._lock:
            self._cache.clear()
            self.logger.info("Cleared credential cache")


class CredentialManager:
    """
    Central credential management system with support for multiple providers.
    
    The CredentialManager coordinates credential access across different
    providers with caching, fallback, and validation support.
    """
    
    def __init__(
        self,
        providers: List[CredentialProvider] = None,
        cache_ttl: int = 300,
        enable_cache: bool = True
    ):
        """
        Initialize the credential manager.
        
        :param providers: List of credential providers to use
        :type providers: List[CredentialProvider]
        :param cache_ttl: Cache time-to-live in seconds
        :type cache_ttl: int
        :param enable_cache: Whether to enable credential caching
        :type enable_cache: bool
        """
        self.logger = logging.getLogger(f"{__name__}.CredentialManager")
        self.providers = providers or []
        self.enable_cache = enable_cache
        self.cache = CredentialCache(default_ttl=cache_ttl) if enable_cache else None
        self._validators: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        
        self.logger.info(
            f"Initialized with {len(self.providers)} provider(s), "
            f"cache: {enable_cache}"
        )
    
    def add_provider(self, provider: CredentialProvider, priority: int = None) -> None:
        """
        Add a credential provider.
        
        :param provider: The credential provider to add
        :type provider: CredentialProvider
        :param priority: Optional priority (lower = higher priority)
        :type priority: int
        """
        with self._lock:
            if priority is not None:
                self.providers.insert(priority, provider)
            else:
                self.providers.append(provider)
        self.logger.info(f"Added provider: {provider.name}")
    
    def remove_provider(self, provider: CredentialProvider) -> None:
        """
        Remove a credential provider.
        
        :param provider: The credential provider to remove
        :type provider: CredentialProvider
        """
        with self._lock:
            if provider in self.providers:
                self.providers.remove(provider)
        self.logger.info(f"Removed provider: {provider.name}")
    
    def register_validator(
        self,
        credential_type: str,
        validator: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Register a validator for a specific credential type.
        
        :param credential_type: The type of credential
        :type credential_type: str
        :param validator: Validation function
        :type validator: Callable
        """
        self._validators[credential_type] = validator
        self.logger.debug(f"Registered validator for type: {credential_type}")
    
    def get_credential(
        self,
        key: str,
        credential_type: str = None,
        use_cache: bool = True,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a credential from available providers.
        
        :param key: The credential key/identifier
        :type key: str
        :param credential_type: Optional credential type for validation
        :type credential_type: str
        :param use_cache: Whether to use cache (if enabled)
        :type use_cache: bool
        :return: The credential data or None if not found
        :rtype: Optional[Dict[str, Any]]
        :raises CredentialNotFoundError: If credential not found in any provider
        :raises CredentialValidationError: If credential validation fails
        """
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        
        # Try each provider in order
        for provider in self.providers:
            try:
                credential = provider.get_credential(key, **kwargs)
                if credential is not None:
                    # Validate if type specified
                    if credential_type and not self._validate_credential_type(
                        credential, credential_type
                    ):
                        self.logger.warning(
                            f"Credential {key} failed type validation: {credential_type}"
                        )
                        continue
                    
                    # Cache if enabled
                    if use_cache and self.cache:
                        self.cache.set(key, credential)
                    
                    self.logger.info(
                        f"Retrieved credential '{key}' from provider: {provider.name}"
                    )
                    return credential
            except CredentialError as e:
                self.logger.warning(
                    f"Provider {provider.name} failed to get credential {key}: {e}"
                )
                continue
        
        # Not found in any provider
        self.logger.error(f"Credential not found: {key}")
        raise CredentialNotFoundError(f"Credential not found: {key}")
    
    def set_credential(
        self,
        key: str,
        value: Dict[str, Any],
        provider_name: str = None,
        credential_type: str = None,
        **kwargs
    ) -> None:
        """
        Store a credential using a specific provider.
        
        :param key: The credential key/identifier
        :type key: str
        :param value: The credential data to store
        :type value: Dict[str, Any]
        :param provider_name: Optional specific provider to use
        :type provider_name: str
        :param credential_type: Optional credential type for validation
        :type credential_type: str
        :raises CredentialValidationError: If validation fails
        :raises CredentialError: If storage fails
        """
        # Validate if type specified
        if credential_type and not self._validate_credential_type(value, credential_type):
            raise CredentialValidationError(
                f"Credential validation failed for type: {credential_type}"
            )
        
        # Find provider
        if provider_name:
            provider = self._find_provider(provider_name)
            if not provider:
                raise CredentialError(f"Provider not found: {provider_name}")
        else:
            # Use first provider
            if not self.providers:
                raise CredentialError("No credential providers available")
            provider = self.providers[0]
        
        # Store credential
        provider.set_credential(key, value, **kwargs)
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate(key)
        
        self.logger.info(f"Stored credential '{key}' using provider: {provider.name}")
    
    def delete_credential(
        self,
        key: str,
        provider_name: str = None,
        **kwargs
    ) -> None:
        """
        Delete a credential.
        
        :param key: The credential key/identifier
        :type key: str
        :param provider_name: Optional specific provider to use
        :type provider_name: str
        """
        if provider_name:
            provider = self._find_provider(provider_name)
            if provider:
                provider.delete_credential(key, **kwargs)
        else:
            # Delete from all providers
            for provider in self.providers:
                try:
                    provider.delete_credential(key, **kwargs)
                except CredentialError:
                    pass
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate(key)
        
        self.logger.info(f"Deleted credential: {key}")
    
    def list_credentials(self, provider_name: str = None) -> List[str]:
        """
        List available credentials.
        
        :param provider_name: Optional specific provider to query
        :type provider_name: str
        :return: List of credential keys
        :rtype: List[str]
        """
        if provider_name:
            provider = self._find_provider(provider_name)
            if provider:
                return provider.list_credentials()
            return []
        else:
            # Collect from all providers
            all_keys = set()
            for provider in self.providers:
                try:
                    keys = provider.list_credentials()
                    all_keys.update(keys)
                except CredentialError as e:
                    self.logger.warning(
                        f"Provider {provider.name} failed to list credentials: {e}"
                    )
            return list(all_keys)
    
    def _find_provider(self, name: str) -> Optional[CredentialProvider]:
        """
        Find a provider by name.
        
        :param name: Provider name
        :type name: str
        :return: The provider or None
        :rtype: Optional[CredentialProvider]
        """
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None
    
    def _validate_credential_type(
        self,
        credential: Dict[str, Any],
        credential_type: str
    ) -> bool:
        """
        Validate a credential against a registered type validator.
        
        :param credential: The credential to validate
        :type credential: Dict[str, Any]
        :param credential_type: The credential type
        :type credential_type: str
        :return: True if valid, False otherwise
        :rtype: bool
        """
        if credential_type not in self._validators:
            self.logger.debug(
                f"No validator registered for type: {credential_type}"
            )
            return True  # No validator, assume valid
        
        validator = self._validators[credential_type]
        try:
            return validator(credential)
        except Exception as e:
            self.logger.error(
                f"Validator for type {credential_type} raised exception: {e}"
            )
            return False


# Global credential manager instance
_global_manager: Optional[CredentialManager] = None
_global_manager_lock = threading.Lock()


def get_credential_manager() -> CredentialManager:
    """
    Get or create the global credential manager instance.
    
    :return: The global credential manager
    :rtype: CredentialManager
    """
    global _global_manager
    
    if _global_manager is None:
        with _global_manager_lock:
            if _global_manager is None:
                _global_manager = _create_default_manager()
    
    return _global_manager


def set_credential_manager(manager: CredentialManager) -> None:
    """
    Set a custom global credential manager.
    
    :param manager: The credential manager to use
    :type manager: CredentialManager
    """
    global _global_manager
    with _global_manager_lock:
        _global_manager = manager


def _create_default_manager() -> CredentialManager:
    """
    Create a default credential manager with standard providers.
    
    :return: Configured credential manager
    :rtype: CredentialManager
    """
    logger = logging.getLogger(f"{__name__}._create_default_manager")
    
    providers = []
    
    # Add environment provider (highest priority)
    try:
        env_provider = EnvironmentCredentialProvider()
        providers.append(env_provider)
        logger.debug("Added environment credential provider")
    except Exception as e:
        logger.warning(f"Failed to create environment provider: {e}")
    
    # Add encrypted file provider if available
    if CRYPTO_AVAILABLE:
        try:
            # Only create if master key is available
            if os.environ.get("LYNGUINE_MASTER_KEY"):
                file_provider = EncryptedFileCredentialProvider()
                providers.append(file_provider)
                logger.debug("Added encrypted file credential provider")
            else:
                logger.debug(
                    "Skipping encrypted file provider (no LYNGUINE_MASTER_KEY)"
                )
        except Exception as e:
            logger.warning(f"Failed to create encrypted file provider: {e}")
    else:
        logger.info(
            "Cryptography not available, encrypted file provider disabled. "
            "Install with: pip install cryptography"
        )
    
    manager = CredentialManager(providers=providers)
    
    # Register standard validators
    manager.register_validator("google_oauth", _validate_google_oauth_credential)
    manager.register_validator("gspread_pandas", _validate_gspread_pandas_credential)
    
    return manager


def _validate_google_oauth_credential(credential: Dict[str, Any]) -> bool:
    """
    Validate Google OAuth credential format.
    
    :param credential: The credential to validate
    :type credential: Dict[str, Any]
    :return: True if valid, False otherwise
    :rtype: bool
    """
    # Google OAuth credentials should have specific fields
    if "value" in credential:
        value = credential["value"]
        if isinstance(value, dict):
            # Check for required OAuth fields
            required_fields = ["client_id", "client_secret"]
            return all(field in value for field in required_fields)
    return False


def _validate_gspread_pandas_credential(credential: Dict[str, Any]) -> bool:
    """
    Validate gspread-pandas credential format.
    
    :param credential: The credential to validate
    :type credential: Dict[str, Any]
    :return: True if valid, False otherwise
    :rtype: bool
    """
    # gspread-pandas typically uses service account JSON
    if "value" in credential:
        value = credential["value"]
        if isinstance(value, dict):
            # Check for service account fields
            required_fields = ["type", "project_id", "private_key", "client_email"]
            return all(field in value for field in required_fields)
    return False


# Convenience functions for common operations

def get_credential(
    key: str,
    credential_type: str = None,
    default: Any = None
) -> Optional[Dict[str, Any]]:
    """
    Get a credential using the global credential manager.
    
    :param key: The credential key/identifier
    :type key: str
    :param credential_type: Optional credential type for validation
    :type credential_type: str
    :param default: Default value if credential not found
    :type default: Any
    :return: The credential data or default
    :rtype: Optional[Dict[str, Any]]
    """
    manager = get_credential_manager()
    try:
        return manager.get_credential(key, credential_type=credential_type)
    except CredentialNotFoundError:
        return default


def set_credential(
    key: str,
    value: Dict[str, Any],
    credential_type: str = None
) -> None:
    """
    Set a credential using the global credential manager.
    
    :param key: The credential key/identifier
    :type key: str
    :param value: The credential data to store
    :type value: Dict[str, Any]
    :param credential_type: Optional credential type for validation
    :type credential_type: str
    """
    manager = get_credential_manager()
    manager.set_credential(key, value, credential_type=credential_type)

