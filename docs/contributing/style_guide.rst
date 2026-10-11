.. _style-guide:

Python Style Guide
==================

Our project adheres to the following style guidelines to ensure consistency and readability in our codebase.

Linting and Formatting with Ruff
--------------------------------

We use `Ruff <https://docs.astral.sh/ruff/>`_ for linting and (planned) formatting.
Ruff replaces the previously documented Black workflow. Configuration lives in
``pyproject.toml`` under ``[tool.ruff]``.

Current baseline (stage 1):

- Target Python version: 3.11
- Line length: 88 characters
- Lint ``select`` starts empty so CI can run Ruff without a mass cleanup
- Format settings prefer double quotes; ``ruff format --check`` is not yet a CI gate

Check locally:

.. code-block:: bash

   poetry run ruff check lynguine

Auto-fix what the active rule set allows (none in stage 1):

.. code-block:: bash

   poetry run ruff check --fix lynguine

Format check / apply (optional locally until gated in CI):

.. code-block:: bash

   poetry run ruff format --check lynguine
   poetry run ruff format lynguine

Follow-up work will enable a narrow rule set (for example ``E4``/``E7``/``E9``/``F``)
and then a format gate once the tree is clean enough.

PEP 8 Compliance
-----------------

In addition to Ruff, we follow the `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python code. This includes guidelines on:

- Naming conventions (variables, functions, classes, etc.).
- Code layout (indentation, imports ordering, whitespace, etc.).
- Programming recommendations (error handling, object type comparisons, etc.).

For a comprehensive list of PEP 8 guidelines, please refer to the official `PEP 8 documentation <https://www.python.org/dev/peps/pep-0008/>`_.
