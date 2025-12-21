Column Management in CustomDataFrame
=====================================

This guide covers how to work with columns in ``CustomDataFrame``, including adding, removing,
and managing column types.

Understanding Column Specifications (colspecs)
----------------------------------------------

CustomDataFrame organizes columns into different types based on their purpose:

**Input Types** (Immutable)
    Read-only data that shouldn't be modified after loading.
    Types: ``input``, ``data``, ``constants``, ``global_consts``

**Output Types** (Mutable, Written to Files)
    Data that will be written to output files.
    Types: ``output``, ``writedata``, ``writeseries``, ``parameters``, ``globals``

**Cache Types** (Mutable, Temporary)
    Intermediate calculations that don't need to be saved.
    Types: ``cache``, ``series_cache``, ``parameter_cache``, ``global_cache``

**Parameter Types** (Global Values)
    Values that are globally valid without an index.
    Types: ``parameters``, ``globals``, ``parameter_cache``, ``global_cache``

**Series Types** (Multiple Rows Per Index)
    Data that may have multiple rows with the same index value.
    Types: ``series``, ``writeseries``, ``series_cache``

Adding Columns
--------------

Method 1: Direct Assignment (Recommended for Quick Operations)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The simplest way to add a column is through direct assignment:

.. code-block:: python

    import pandas as pd
    from lynguine.assess.data import CustomDataFrame
    
    # Create a dataframe
    df = CustomDataFrame(pd.DataFrame({'A': [1, 2, 3]}))
    
    # Add a column using direct assignment (goes to 'cache' by default)
    df['B'] = [4, 5, 6]
    
    # You can also use pandas Series
    df['C'] = pd.Series([7, 8, 9], index=df.index)

Direct assignment automatically adds the column to the ``cache`` colspec type,
making it mutable but not saved to output files.

Method 2: add_column() Method (Recommended for Explicit Type Control)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``add_column()`` when you need explicit control over the column type:

.. code-block:: python

    # Add a column with default type (cache)
    df.add_column('new_col', [10, 11, 12])
    
    # Add a column as output type (will be written to files)
    df.add_column('result', [13, 14, 15], colspec='output')
    
    # Add a parameter (global value)
    df.add_column('threshold', [0.5, 0.5, 0.5], colspec='parameters')

**Advantages of add_column():**

* Explicit type specification
* Validation that column doesn't already exist
* Validation that colspec type is valid
* Self-documenting code

Removing Columns
----------------

Use the ``drop_column()`` method to remove columns:

.. code-block:: python

    # Drop a single column
    df.drop_column('unwanted_col')
    
    # The column is removed from both the data and column specifications

**Note:** This permanently removes the column. There is no undo.

Common Patterns
---------------

Pattern 1: Pre-creating Columns for Compute Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some compute operations expect columns to exist:

.. code-block:: python

    # Pre-create columns that compute operations will populate
    df['word_count'] = None
    df['sentiment_score'] = None
    
    # Then run compute operations that fill these columns
    df.compute.run()

Pattern 2: Converting Column Types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To move a column to a different colspec type:

.. code-block:: python

    # Save the data
    col_data = df['temp_col']
    
    # Drop from current location
    df.drop_column('temp_col')
    
    # Re-add with new type
    df.add_column('temp_col', col_data, colspec='output')

Pattern 3: Working with Series Data (Multiple Rows Per Index)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For data with multiple rows per index value:

.. code-block:: python

    # Create a series with repeated indices
    series_data = pd.Series([1, 2, 3, 4], index=['a', 'a', 'b', 'b'])
    
    # This automatically goes to a series-type colspec
    df['multi_value_col'] = series_data

Best Practices
--------------

1. **Use add_column() for clarity**: When the column type matters, use ``add_column()``
   with an explicit ``colspec`` parameter.

2. **Use direct assignment for quick work**: For temporary calculations or when working
   interactively, direct assignment (``df['col'] = value``) is more concise.

3. **Choose the right colspec type**:
   
   * Use ``input`` for source data that shouldn't change
   * Use ``output`` for results you want to save
   * Use ``cache`` for intermediate calculations
   * Use ``parameters`` for global configuration values

4. **Validate before dropping**: Check if a column exists before dropping to avoid errors:

   .. code-block:: python

       if 'col_name' in df.columns:
           df.drop_column('col_name')

Common Errors and Solutions
----------------------------

Error: Column already exists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # ❌ This raises ValueError
    df.add_column('existing_col', [1, 2, 3])

**Solution**: Use direct assignment to replace values, or drop first:

.. code-block:: python

    # ✅ Replace values
    df['existing_col'] = [1, 2, 3]
    
    # ✅ Or drop and re-add
    df.drop_column('existing_col')
    df.add_column('existing_col', [1, 2, 3], colspec='output')

Error: Column not found
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # ❌ This raises KeyError
    df.drop_column('nonexistent_col')

**Solution**: Check if column exists first:

.. code-block:: python

    # ✅ Check first
    if 'nonexistent_col' in df.columns:
        df.drop_column('nonexistent_col')

Error: Invalid colspec
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # ❌ This raises ValueError
    df.add_column('col', [1, 2, 3], colspec='invalid_type')

**Solution**: Use one of the valid colspec types listed at the top of this guide.

Related Documentation
---------------------

* :class:`lynguine.assess.data.CustomDataFrame` - Full API documentation
* :meth:`lynguine.assess.data.CustomDataFrame.add_column` - Add column method
* :meth:`lynguine.assess.data.CustomDataFrame.drop_column` - Drop column method
* :doc:`compute_framework` - Using columns with compute operations

