Setup for Development
=====================

Setting up a development environment is crucial for contributing to the project. Follow these steps to get started:

Install Dependencies
--------------------

Our project uses `uv <https://docs.astral.sh/uv/>`_ for managing dependencies. To install them, navigate to the project's root directory and run:

.. code-block:: bash

    uv sync --extra documents --extra parquet --group dev

Setting Up a Virtual Environment
--------------------------------

``uv sync`` creates a virtual environment for your project (``.venv`` by default). To run commands in that environment without activating it:

.. code-block:: bash

    uv run pytest

Or activate it in your shell:

.. code-block:: bash

    source .venv/bin/activate

You can now start developing for the project within this virtual environment.

Configuring Your Development Environment
----------------------------------------

- Configure your IDE or text editor to adhere to Python's PEP 8 style guide.
- Ensure that your editor respects the `.editorconfig` file at the project's root, if present.
- Set up pre-commit hooks, if used, by running `pre-commit install`.
