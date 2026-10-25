Examples
========

These examples run against lynguine as installed. They do not need extra files in the repository.

Load a local table
------------------

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
    print(data.get_column_type("score"))

Write and read BibTeX
---------------------

PMLR papers publish a ``.bib`` file. After that file is on disk, ``io`` loads it. The same path works for a file you generate:

.. code-block:: python

    import pandas as pd
    from lynguine.access.io import read_bibtex, write_bibtex
    from lynguine.util import fake

    fake.random.seed(1)
    details = {"filename": "sample.bib", "directory": "."}
    entries = [fake.to_bibtex(fake.bibliography_entry()) for _ in range(3)]
    write_bibtex(pd.DataFrame(entries), details)
    df, details = read_bibtex(details)
    print(df[["ID", "ENTRYTYPE", "year"]])

Further reading
---------------

* :doc:`quickstart` — the local-flow example with a short commentary
* :doc:`column_management` — ``add_column``, ``drop_column``, colspecs
* :doc:`stacking` — joining sources
* :doc:`directory_sources` — directory readers
