Setup for Development
=====================

Setting up a development environment is crucial for contributing to the project. Follow these steps to get started:

Install Dependencies
--------------------

Our project uses Poetry for managing dependencies. To install them, navigate to the project's root directory and run:

.. code-block:: bash

    poetry install

Setting Up a Virtual Environment
--------------------------------

Poetry automatically creates a virtual environment for your project. To activate it, run:

.. code-block:: bash

    poetry shell

You can now start developing for the project within this virtual environment.

Configuring Your Development Environment
----------------------------------------

- Configure your IDE or text editor to adhere to Python's PEP 8 style guide.
- Ensure that your editor respects the `.editorconfig` file at the project's root, if present.
- Set up pre-commit hooks, if used, by running `pre-commit install`.

