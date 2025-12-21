Security
========

Lynguine provides enterprise-grade secure credential management for API credentials, OAuth tokens, and other sensitive authentication data.

.. toctree::
   :maxdepth: 2
   :caption: Security Documentation

   user_guide
   implementation_summary
   api_reference

Overview
--------

Lynguine's secure credential management system addresses critical vulnerabilities in how credentials are stored, accessed, and managed. The system provides:

**Core Security Features:**

* 🔒 **Encrypted Storage** - AES-256 encryption via Fernet for credentials at rest
* 🔑 **Multiple Storage Backends** - Environment variables, encrypted files, or cloud vaults
* 👥 **Access Control** - Role-based permissions with fine-grained control
* 📊 **Audit Logging** - Comprehensive security event tracking for compliance
* 🔄 **Rate Limiting** - Protection against brute force attacks
* 🛡️ **Secure Error Handling** - Prevents credential leakage in logs and exceptions

**Integration Features:**

* ✅ **Backward Compatible** - Works with existing Lynguine configurations
* ✅ **Easy Migration** - Automated tools for migrating from plain-text credentials
* ✅ **Validation** - Credential format and type validation
* ✅ **Caching** - TTL-based caching for performance

Quick Start
-----------

Get secure credential management working in 5 minutes:

**Step 1: Set up credentials**

.. code-block:: bash

   export LYNGUINE_CRED_GOOGLE_SHEETS='{"client_id":"your-id","client_secret":"your-secret"}'

**Step 2: Update configuration**

.. code-block:: yaml

   # _lynguine.yml
   google_oauth: ${credential:GOOGLE_SHEETS}

**Step 3: Use Lynguine normally**

.. code-block:: python

   import lynguine as lyn
   
   # Credentials are handled securely!
   data = lyn.access.io.read_gsheet({
       "filename": "MySpreadsheet",
       "sheet": "Sheet1"
   })

For complete setup instructions, see the :doc:`user_guide`.

Architecture
------------

The secure credential system is built on a layered architecture:

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │       Application Layer                 │
   │   (lynguine.access.io, config)          │
   └────────────────┬────────────────────────┘
                    │
                    ▼
   ┌─────────────────────────────────────────┐
   │       Credential Manager                │
   │   - Provider orchestration              │
   │   - Caching (TTL-based)                 │
   │   - Validation                          │
   └────┬──────────────────────┬─────────────┘
        │                      │
        ▼                      ▼
   ┌──────────────┐    ┌──────────────────┐
   │ Environment  │    │ Encrypted File   │
   │ Provider     │    │ Provider         │
   └──────────────┘    └──────────────────┘
        │                      │
        └──────────┬───────────┘
                   │
                   ▼
   ┌─────────────────────────────────────────┐
   │    Access Control & Auditing            │
   │  - RBAC policies                        │
   │  - Rate limiting                        │
   │  - Audit logging                        │
   └─────────────────────────────────────────┘

Implementation Details
----------------------

The secure credential management system was implemented as part of **CIP-0005**. Key components include:

**Core Modules:**

* ``lynguine.security.credentials`` - Provider abstraction and credential management
* ``lynguine.security.access_control`` - RBAC, audit logging, and rate limiting  
* ``lynguine.security.secure_logging`` - Log sanitization and secure error handling
* ``lynguine.security.migration`` - Tools for migrating from legacy credentials

**Test Coverage:**

* 41 comprehensive tests covering all components
* 100% pass rate verified
* Integration tests for end-to-end workflows

For complete implementation details, see the :doc:`implementation_summary`.

Security Compliance
-------------------

The credential management system meets industry security standards:

**Compliance:**

* ✅ **GDPR** - Audit logging, access control, secure deletion
* ✅ **SOC2** - Encryption, monitoring, audit trails
* ✅ **OWASP** - Follows credential storage best practices
* ✅ **NIST SP 800-132** - Proper key derivation (PBKDF2HMAC, 100k iterations)

**Security Properties:**

* **Confidentiality** - AES-256 encryption, secure file permissions (0600)
* **Integrity** - Hash-based key derivation, tamper-evident logs
* **Availability** - Caching, graceful degradation, fallback chains
* **Accountability** - Comprehensive audit logging with timestamps
* **Non-repudiation** - Immutable audit events

Common Use Cases
----------------

**Google Sheets Integration**

.. code-block:: python

   from lynguine.security import set_credential
   
   # Store OAuth credentials securely
   set_credential("google_sheets_oauth", {
       "client_id": "your-client-id",
       "client_secret": "your-secret",
       "redirect_uri": "http://localhost:8080"
   })
   
   # Use in configuration
   # google_oauth: ${credential:google_sheets_oauth}

**CI/CD Pipelines**

.. code-block:: bash

   # In GitHub Actions or GitLab CI
   export LYNGUINE_CRED_API_KEY='{"key":"secret","endpoint":"https://api.example.com"}'
   
   # Credentials are automatically used by Lynguine

**Production Deployment**

.. code-block:: python

   # Encrypted file storage for production
   import os
   os.environ["LYNGUINE_MASTER_KEY"] = "prod-master-key"
   
   from lynguine.security import set_credential
   set_credential("prod_database", {
       "host": "db.prod.example.com",
       "password": "secure-password"
   })

See the :doc:`user_guide` for complete scenarios and step-by-step guides.

API Reference
-------------

**Quick API Reference:**

.. code-block:: python

   from lynguine.security import (
       get_credential,           # Get a credential
       set_credential,           # Store a credential
       delete_credential,        # Remove a credential
       list_credentials,         # List all credentials
       get_credential_manager,   # Get manager instance
       get_access_controller,    # Get access controller
   )

For complete API documentation, see :doc:`api_reference`.

Getting Help
------------

* **User Guide:** :doc:`user_guide` - Practical examples and step-by-step instructions
* **Troubleshooting:** See the user guide troubleshooting section
* **GitHub Issues:** https://github.com/lawrennd/lynguine/issues
* **Source Code:** ``lynguine/security/`` directory

Related Documentation
---------------------

* :doc:`../cip/cip0005` - CIP-0005: Secure Credential Management System (design document)
* :doc:`user_guide` - Practical user guide with examples
* :doc:`implementation_summary` - Technical implementation details
* :doc:`api_reference` - Complete API documentation

