.. _contributing:

Python Style Guide
==================

Our project adheres to the following style guidelines to ensure consistency and readability in our codebase.

Code Formatting with Black
--------------------------

We use `Black <https://github.com/psf/black>`_ for automatic code formatting. Black enforces a style that conforms to PEP 8, with some adjustments for improved readability and reduced line length debates. Here are the key aspects:

- Line length is limited to 88 characters.
- Black reformats entire blocks of code in a deterministic way.
- Double quotes are preferred over single quotes.

To format your code with Black, run:

.. code-block:: bash

    black your_script.py

or for an entire directory:

.. code-block:: bash

    black your_directory

PEP 8 Compliance
----------------

In addition to Black's formatting, we follow the `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python code. This includes guidelines on:

- Naming conventions (variables, functions, classes, etc.).
- Code layout (indentation, imports ordering, whitespace, etc.).
- Programming recommendations (error handling, object type comparisons, etc.).

For a comprehensive list of PEP 8 guidelines, please refer to the official `PEP 8 documentation <https://www.python.org/dev/peps/pep-0008/>`_.

