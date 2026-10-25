Quick Start Guide
=================

Install lynguine, then load a small local table through an interface YAML flow.

Creating a CustomDataFrame from a flow
--------------------------------------

.. code-block:: python

    from lynguine.config.interface import Interface
    from lynguine.assess.data import CustomDataFrame

    interface = Interface.from_yaml("""
    input:
      type: local
      index: name
      data:
        - name: Ada
          score: 1
        - name: Alan
          score: 2
      compute:
        - field: accessDate
          function: today
    """)

    data = CustomDataFrame.from_flow(interface)
    print(data)

``today`` is a registered compute function. It adds an ``accessDate`` column while the table is loaded.

Exploring further
-----------------

* :doc:`examples` — BibTeX write/read and the same local-flow pattern
* :doc:`column_management` — adding and typing columns
* :doc:`stacking` — ``hstack`` / ``vstack``
* :doc:`directory_sources` — one row per file
