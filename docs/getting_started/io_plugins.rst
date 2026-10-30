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

Contract
--------

Register from the plugin package (typically at import time)::

   from lynguine.access.io import register_io_type
   import pandas as pd

   def read_cards(details):
       # details is the YAML mapping for this item (type, board, …)
       # Resolve secrets with CIP-0005; do not put tokens in YAML.
       return pd.DataFrame(...)  # one row per card / message / row

   register_io_type("trello", read=read_cards)

``read`` must return a ``pandas.DataFrame``. ``write`` is optional. The
default is **read-only**. A writer runs only when both are true:

* ``register_io_type(..., write=write_fn)``
* the flow item sets ``write: true``

Otherwise ``write_data`` raises ``Type "trello" is read-only`` and does
not fall through to a file writer.

Builtin names cannot be overwritten. Registering ``csv`` or ``gsheet``
raises ``ReservedIOTypeError``.

Loading a plugin
----------------

**Explicit import list** (preferred). The interface names modules before
any ``read_data``::

   plugins:
     - lynguine_trello

   allocation:
     type: trello
     board: "2026-panel"
     index: id

Failed imports name the module.

**In-process registration** is enough for tests and for apps that import
the plugin themselves.

**Optional entry points.** Group ``lynguine.io_types``, key equal to the
``type:`` name. Lynguine loads that entry only when that type is
requested and is not already registered. ``import lynguine`` does not
scan plugins.

Zero-plugin path
----------------

Export the live store to YAML or CSV and use a builtin ``type:``. Plugins
are for when the live store is the authoritative input.

Credentials
-----------

Use the existing credential system (CIP-0005 / REQ-0004). Interface YAML
holds board names, mailboxes, and field lists — not tokens.

What this is not
----------------

* Not CIP-0013 ``register_strategy`` (documents → units).
* Not CIP-0009 ``source.type`` (download a file, then read it).
* Not referia ``type: email`` outbound drafts.
* Not a marketplace. There is no version negotiation beyond importing
  the module you depend on.
