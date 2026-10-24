Stacking and joining sources
============================

Lynguine combines sources with ``hstack`` (side by side) and ``vstack``
(one below the other). When several sources or flows share column names,
the join rule is explicit: **earlier wins**. Later colliding columns are
dropped rather than raising a pandas overlap error.

Horizontal stacking (``hstack``)
--------------------------------

``hstack`` aligns sources on a common key or index so each source
contributes columns for the same rows.

Required keys:

* ``type``: ``hstack``
* ``specifications``: list of nested source blocks

Optional keys (defaults shown):

* ``on``: join key (default ``index``)
* ``how``: ``left``, ``right``, ``outer``, or ``inner`` (default ``left``)
* ``lsuffix``: suffix for overlapping left columns (default empty)
* ``rsuffix``: suffix for overlapping right columns (default ``_right``)

Two-way overlap keeps the left name and suffixes the right. A later
source that would recreate an existing suffixed name is dropped.

.. code-block:: yaml

   type: hstack
   specifications:
     - type: csv
       filename: data/people.csv
     - type: excel
       filename: data/scores.xlsx
       sheet: Sheet1
       on: id
       how: left

Vertical stacking (``vstack``)
------------------------------

``vstack`` concatenates sources that share a column set.

* ``type``: ``vstack``
* ``specifications``: list of nested source blocks
* ``reset_index``: reset after concat (default ``false``)

You can nest ``hstack`` inside ``vstack`` (and the reverse).

Earlier-wins on overlapping columns
-----------------------------------

The same policy applies at two sites:

==================== ==========================================================
Site                 Behaviour
==================== ==========================================================
``read_hstack``      Before ``join`` / ``merge``, drop right columns whose
                     ``{col}{rsuffix}`` (default ``_right``) already exists on
                     the left. Two-way ``B`` → ``B_right`` is unchanged.
``to_pandas()``      Before ``join(how="outer")``, drop right columns already
                     present on the left. If the right frame is then empty,
                     join an empty frame so the index still aligns. Parameter
                     flows still use ``assign``.
==================== ==========================================================

Identity columns such as ``crsid`` or ``givenName`` often appear on more
than two sources. The first occurrence is kept. Later copies are not
suffixed again and are not merged in.

See :meth:`lynguine.access.io.read_hstack` and
:meth:`lynguine.assess.data.CustomDataFrame.to_pandas`.
Column types and mappings are covered in
:doc:`column_management`.
