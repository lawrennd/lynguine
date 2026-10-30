Writing a tabular IO plugin
===========================

Lynguine reads and writes tables through ``type:`` on a flow item
(``allocation``, ``input``, ``output``, …). Builtin names (``csv``,
``excel``, ``yaml``, directory types, ``gsheet``, …) stay in the core
package. A **plugin** implements another name in a separate package so
lynguine does not grow a vendor SDK.

This hook is **CIP-0019**. It is the table-store sibling of CIP-0013
document strategies. Use CIP-0013 when the source is a document (PDF,
DOCX, Google Docs body). Use CIP-0009 ``source:`` when the job is
fetch-then-read a file (HTTP or GitHub). Use CIP-0019 when the
authoritative store is a live API or query that should become a
DataFrame.

Point a new package at this page. Copy the skeleton below, change the
type name, credential kind, and SDK calls.

Contract
--------

Register from the plugin package at import time::

   from lynguine.access.io import register_io_type
   from lynguine.security.credentials import get_credential_manager

   def validate_trello_api(credential):
       value = credential.get("value", credential)
       if isinstance(value, dict):
           return "api_key" in value and "token" in value
       return False

   get_credential_manager().register_validator("trello_api", validate_trello_api)

   def read_cards(details):
       creds = details["credential_value"]  # injected by lynguine
       # creds is the stored payload, e.g. {"api_key": ..., "token": ...}
       # Call the vendor SDK. Return one row per card / message / result.
       import pandas as pd
       return pd.DataFrame(...)

   register_io_type(
       "trello",
       read=read_cards,
       credential_type="trello_api",
   )

``read`` must return a ``pandas.DataFrame``. ``write`` is optional. The
default is **read-only**. A writer runs only when both are true:

* ``register_io_type(..., write=write_fn)``
* the flow item sets ``write: true``

Otherwise ``write_data`` raises ``Type "trello" is read-only`` and does
not fall through to a file writer.

Builtin names cannot be overwritten. Registering ``csv`` or ``gsheet``
raises ``ReservedIOTypeError``.

Authorisation
-------------

The plugin **declares** the credential kind. Lynguine **fetches** the
secret (CIP-0005). The plugin must not read tokens from YAML and should
not call ``CredentialManager.get_credential`` itself.

+----------------------+--------------------------------------------+
| Who                  | What                                       |
+======================+============================================+
| Plugin import        | ``register_validator("trello_api", ...)``  |
|                      | and ``credential_type="trello_api"``       |
+----------------------+--------------------------------------------+
| Flow YAML            | ``credential: my_trello`` (a **key** name) |
+----------------------+--------------------------------------------+
| Lynguine             | ``authorize_access``, then                 |
|                      | ``get_credential(key, credential_type=)``  |
|                      | → ``details["credential_value"]``          |
+----------------------+--------------------------------------------+
| Plugin ``read``      | Uses ``details["credential_value"]`` only  |
+----------------------+--------------------------------------------+

Reuse ``google_oauth`` for Gmail or Google Docs rather than inventing a
second Google secret format. Types that need no secret omit
``credential_type`` (the default).

YAML for a live store::

   plugins:
     - lynguine_trello

   allocation:
     type: trello
     board: "2026-panel"
     index: id
     credential: my_trello

Store the secret once with CIP-0005 (environment or encrypted file), not
in the interface. See :doc:`../security/index`.

Loading a plugin
----------------

**Explicit import list** (preferred). The interface names modules before
any ``read_data``::

   plugins:
     - lynguine_trello

Failed imports name the module.

**In-process registration** is enough for tests and for apps that import
the plugin themselves.

**Optional entry points.** In the plugin's ``pyproject.toml``::

   [project.entry-points."lynguine.io_types"]
   trello = "lynguine_trello:register"

The callable (or module import) must call ``register_io_type`` for that
type name. Lynguine loads that entry only when that type is requested
and is not already registered. ``import lynguine`` does not scan
plugins.

Package layout
--------------

A plugin package is ordinary Python. Minimum files::

   lynguine_trello/
     __init__.py    # register validator + register_io_type
   pyproject.toml   # depends on lynguine; optional entry point above
   tests/
     test_read.py   # mock credential_value; no network in CI

``__init__.py`` can expose ``register()`` for the entry point, which
calls the same registration already run at import.

Zero-plugin path
----------------

Export the live store to YAML or CSV and use a builtin ``type:``. Plugins
are for when the live store is the authoritative input.

What this is not
----------------

* Not CIP-0013 ``register_strategy`` (documents → units).
* Not CIP-0009 ``source.type`` (download a file, then read it).
* Not referia ``type: email`` outbound drafts.
* Not a marketplace. There is no version negotiation beyond importing
  the module you depend on.
