# This file loads configurations that are specific to the context
import os
import yaml
import re
from itertools import chain

# Import secure credential management
try:
    from ..security.credentials import (
        get_credential_manager,
        CredentialNotFoundError,
        CredentialValidationError
    )
    SECURE_CREDENTIALS_AVAILABLE = True
except ImportError:
    SECURE_CREDENTIALS_AVAILABLE = False

class _Config(object):
    """
    Base class for context and settings objects.

    This class is designed to be inherited, not used directly.
    """
    def __init__(self):
        raise NotImplementedError("The base object _Config is designed to be inherited")
    
    def __getitem__(self, key):
        """
        Return the value of the key.
        :param key: The key to be returned.
        :type key: str
        :return: The value of the key.
        """
        return self._data[key]            

    def __setitem__(self, key, value):
        """
        Set the value of the key.
        :param key: The key to be set.
        :type key: str
        :param value: The value to be set.
        :type value: object
        :return: None
        """
        self._data[key] = value

    def __delitem__(self, key):
        """
        Delete the key.

        :param key: The key to be deleted.
        :type key: str
        :return: None
        """
        del self._data[key]

    def __iter__(self):
        """
        Return an iterator over the keys.

        :return: An iterator over the keys.
        """
        return iter(self._data)

    def __len__(self):
        """
        Return the number of keys.

        :return: The number of keys.
        :rtype: int
        """
        return len(self._data)

    def __contains__(self, key):
        """
        Check if the key is in the object.
        
        :param key: The key to be checked.
        :type key: str
        :return: True if the key is in the object, False otherwise.
        :rtype: bool
        """
        return key in self._data 

    def keys(self):
        """
        Return the keys.

        :return: The keys.
        :rtype: list
        """
        return self._data.keys()

    def items(self):
        """
        Return the items.

        :return: The items.
        :rtype: list
        """
        return self._data.items()

    def values(self):
        """
        Return the values.

        :return: The values.
        :rtype: list
        """
        return self._data.values()

    def get(self, key, default=None):
        """
        Return the value of the key, or the default if the key is not found.

        :param key: The key to be returned.
        :type key: str
        :param default: The default value to be returned if the key is not found.
        :type default: object
        :return: The value of the key, or the default if the key is not found.
        :rtype: object
        """
        return self._data.get(key, default)

    def update(self, *args, **kwargs):
        """
        Update the object with the values from another object.

        :param args: The object to be updated with.
        :type args: object
        :param kwargs: The object to be updated with.
        :type kwargs: object
        :return: None
        """
        self._data.update(*args, **kwargs)
        
    def __str__(self):
        """
        Return a string representation of the object.

        :return: A string representation of the object.
        :rtype: str
        """
        return str(self._data)

    def __repr__(self):
        """
        Return a string representation of the object.

        :return: A string representation of the object.
        """
        return f"{self.__class__.__name__}({self._data})"

class Context(_Config):
    """
    Load in some default configuration from the context.
    """
    def __init__(self, name=None, data=None):
        """
        Load in the configuration from the context.

        :param name: The name of the context.
        :type name: str
        :raises ValueError: If no configuration file is found.
        """
        
        # Load in the default configuration
        self._default_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "defaults.yml"))
        # Load in the local configuration
        self._local_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "machine.yml"))

        if name is None:
            name = __name__
        self._name = name
        self._data = {}

        if data is not None:
            self._data = data
        else:
            
            if os.path.exists(self._default_file):
                with open(self._default_file) as file:
                    self._data.update(yaml.safe_load(file))

            if os.path.exists(self._local_file):
                with open(self._local_file) as file:
                    self._data.update(yaml.safe_load(file))

        # If there's no configuration, raise an error
        if self._data=={}:
            raise ValueError(
                "No configuration file found at either "
                + self._local_file
                + " or "
                + self._default_file
                + "."
            )
        self._expand_vars()
        self._add_logging_defaults()

    def _expand_vars(self):
        """
        Expand environment variables and credential references in configuration.
        
        Supports:
        - Environment variables: $VAR or ${VAR}
        - Credential references: ${credential:key_name}

        :return: None
        """
        for key, item in self._data.items():
            self._data[key] = self._expand_value(item)
    
    def _expand_value(self, value):
        """
        Recursively expand a configuration value.
        
        :param value: The value to expand
        :return: The expanded value
        """
        if isinstance(value, str):
            # Expand credential references first
            value = self._expand_credential_references(value)
            # Then expand environment variables
            value = os.path.expandvars(value)
            return value
        elif isinstance(value, dict):
            return {k: self._expand_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_value(item) for item in value]
        else:
            return value
    
    def _expand_credential_references(self, value):
        """
        Expand credential references in a string value.
        
        Credential references have the format: ${credential:key_name}
        
        :param value: The string value to expand
        :type value: str
        :return: The expanded value
        :rtype: str
        """
        if not isinstance(value, str):
            return value
        
        # Pattern to match ${credential:key_name}
        pattern = r'\$\{credential:([^}]+)\}'
        
        def replace_credential(match):
            credential_key = match.group(1)
            
            if not SECURE_CREDENTIALS_AVAILABLE:
                # If secure credentials not available, return the reference unchanged
                return match.group(0)
            
            try:
                credential_manager = get_credential_manager()
                credential = credential_manager.get_credential(credential_key)
                
                if credential and "value" in credential:
                    cred_value = credential["value"]
                    # If the credential value is a dict, return it as-is
                    # (will be handled by caller)
                    if isinstance(cred_value, dict):
                        # For string replacement, we can't embed a dict
                        # Return a placeholder that indicates success
                        return f"__CREDENTIAL_DICT_{credential_key}__"
                    else:
                        # For simple values, return the string representation
                        return str(cred_value)
                else:
                    raise CredentialNotFoundError(
                        f"Credential '{credential_key}' has no value"
                    )
            except (CredentialNotFoundError, CredentialValidationError) as e:
                # Log warning but don't fail - return the original reference
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to resolve credential reference '{credential_key}': {e}"
                )
                return match.group(0)
        
        # Replace all credential references
        expanded = re.sub(pattern, replace_credential, value)
        
        # If the entire value is a credential dict placeholder, fetch and return the dict
        if expanded.startswith("__CREDENTIAL_DICT_") and expanded.endswith("__"):
            credential_key = expanded[18:-2]  # Extract key from placeholder
            try:
                credential_manager = get_credential_manager()
                credential = credential_manager.get_credential(credential_key)
                if credential and "value" in credential:
                    return credential["value"]
            except Exception:
                pass
        
        return expanded

    def _add_logging_defaults(self):
        """
        If there's no logging information in files, add some default info.
        """
        default_log = self._name + ".log"
        if "logging" in self._data:
            if not "level" in self._data["logging"]:
                self._data["logging"]["level"] = 20
                
            if not "filename" in self._data["logging"]:
                self._data["logging"]["filename"] = default_log
        else:
            self._data["logging"] = {"level": 20, "filename": default_log}

            
