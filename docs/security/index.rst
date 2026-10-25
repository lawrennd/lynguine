Credentials
===========

Most lynguine flows read local files and need no secrets. If a source is authenticated (Google Sheets is the usual case), configuration can name a credential with ``${credential:KEY}`` instead of putting a secret in YAML.

Shipped backends
----------------

* **Environment variables** — ``LYNGUINE_CRED_<KEY>`` (JSON). Fits CI and one-off shells.
* **Encrypted files** — Fernet/AES-256 under ``~/.lynguine/credentials/``, unlocked with ``LYNGUINE_MASTER_KEY``. Needs the ``cryptography`` extra.

There is no cloud-vault provider. OS keychain storage is not implemented (backlog ``2025-12-22_os-keychain-master-key-storage``).

Minimal example
---------------

.. code-block:: bash

   export LYNGUINE_CRED_GOOGLE_SHEETS='{"client_id":"your-id","client_secret":"your-secret"}'

.. code-block:: yaml

   google_oauth: ${credential:GOOGLE_SHEETS}

The same key is what ``lynguine.security.get_credential`` looks up. Log lines fingerprint identifiers rather than printing them (CIP-000B).

Further reading
---------------

.. toctree::
   :maxdepth: 1

   user_guide
   api_reference

* CIP-0005 in the repository (``cip/cip0005.md``) is the design record, not a user guide.
