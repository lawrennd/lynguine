Installation Guide
==================

This guide will walk you through the process of installing lynguine.

Prerequisites
-------------

Ensure you have Python 3.11 or later installed on your system. You can download Python from `python.org <https://www.python.org/downloads/>`_.

Installing lynguine
-------------------

ndlpy can be installed using pip. Run the following command:

.. code-block:: bash

    pip install lynguine

Alternatively, if you are installing from source:

.. code-block:: bash

    git clone https://github.com/lawrennd/lynguine.git
    cd ndlpy
    pip install .

Verify the installation:

.. code-block:: bash

    python -c "import lynguine; print(lynguine.__version__)"
