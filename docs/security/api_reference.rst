API Reference
=============

This page provides the complete API reference for Lynguine's secure credential management system.

Core Functions
--------------

.. automodule:: lynguine.security
   :members:
   :undoc-members:
   :show-inheritance:

Credential Providers
--------------------

.. automodule:: lynguine.security.credentials
   :members:
   :undoc-members:
   :show-inheritance:

Access Control
--------------

.. automodule:: lynguine.security.access_control
   :members:
   :undoc-members:
   :show-inheritance:

Secure Logging
--------------

.. automodule:: lynguine.security.secure_logging
   :members:
   :undoc-members:
   :show-inheritance:

Migration Tools
---------------

.. automodule:: lynguine.security.migration
   :members:
   :undoc-members:
   :show-inheritance:

Quick Reference
---------------

Core Functions
~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.security import (
       get_credential,           # Get a credential
       set_credential,           # Store a credential  
       delete_credential,        # Remove a credential
       list_credentials,         # List all credentials
       get_credential_manager,   # Get manager instance
       get_access_controller,    # Get access controller
   )

Providers
~~~~~~~~~

.. code-block:: python

   from lynguine.security import (
       EnvironmentCredentialProvider,     # Environment variables
       EncryptedFileCredentialProvider,   # Encrypted files
       CredentialProvider,                # Base class for custom providers
   )

Access Control
~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.security import (
       AccessLevel,              # Access level enum
       AccessPolicy,             # Access control policy
       RateLimiter,             # Rate limiting
       CredentialAccessController,  # Unified access control
   )

Exceptions
~~~~~~~~~~

.. code-block:: python

   from lynguine.security import (
       CredentialError,              # Base exception
       CredentialNotFoundError,      # Credential missing
       CredentialValidationError,    # Invalid credential
       CredentialEncryptionError,    # Encryption failed
       AccessDeniedError,            # Access denied
       RateLimitError,              # Rate limit exceeded
   )

Logging
~~~~~~~

.. code-block:: python

   from lynguine.security import (
       SecureLogger,            # Secure logging wrapper
       SanitizingFormatter,     # Log sanitization
       SecureExceptionHandler,  # Exception sanitization
   )

Migration
~~~~~~~~~

.. code-block:: python

   from lynguine.security.migration import (
       CredentialMigrator,      # Migration tool
   )

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from lynguine.security import get_credential, set_credential
   
   # Store a credential
   set_credential("my_api_key", {
       "key": "secret123",
       "endpoint": "https://api.example.com"
   })
   
   # Retrieve a credential
   creds = get_credential("my_api_key")
   api_key = creds["value"]["key"]

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set credential as environment variable
   export LYNGUINE_CRED_MY_KEY='{"api_key":"secret","endpoint":"https://api.example.com"}'

.. code-block:: python

   from lynguine.security import get_credential
   
   # Automatically retrieved from environment
   creds = get_credential("MY_KEY")

Encrypted Storage
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import os
   from lynguine.security import set_credential
   
   # Set master key
   os.environ["LYNGUINE_MASTER_KEY"] = "your-secure-password"
   
   # Store encrypted credential
   set_credential("google_sheets", {
       "client_id": "...",
       "client_secret": "..."
   })

Access Control
~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.security import (
       get_access_controller,
       AccessPolicy,
       AccessLevel
   )
   
   controller = get_access_controller()
   policy = AccessPolicy()
   
   # Add access rule
   policy.add_rule(
       credential_pattern="prod_*",
       user_pattern="admin",
       access_level=AccessLevel.ADMIN
   )
   
   controller.set_policy(policy)

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from lynguine.security import (
       get_credential,
       CredentialNotFoundError
   )
   
   try:
       creds = get_credential("my_key")
   except CredentialNotFoundError:
       print("Credential not found - please configure MY_KEY")
       # Handle missing credential

See Also
--------

* :doc:`user_guide` - Complete user guide with step-by-step instructions
* :doc:`implementation_summary` - Technical implementation details
* :doc:`index` - Security documentation overview

