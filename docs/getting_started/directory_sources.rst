Directory of files
==================

Directory readers allocate **one row per matched file**. Choose a typed
reader for the file format. Discovery is non-recursive unless you set
``recursive: true``. Field projection is opt-in with ``fields``.

Typed readers
-------------

====================== ============= ===========================
Type                   Default glob  Reader
====================== ============= ===========================
``yaml_directory``     ``*.yml``     YAML mappings
``json_directory``     ``*.json``    JSON mappings
``markdown_directory`` ``*.md``      Markdown (+ front matter)
``bibtex_directory``   ``*.bib``     BibTeX
``docx_directory``     ``*.docx``    Word documents
``directory``          ``*``         Plain / auto by extension
``meta_directory``     ``*``         Sidecar YAML meta files
====================== ============= ===========================

Shared options
--------------

Each ``source`` entry (or, for ``recursive`` / ``fields``, the top-level
details when omitted per source) accepts:

.. code-block:: yaml

   type: yaml_directory
   source:
     - directory: path/to/directory
       glob: "*.yml"
       regexp: "^cfg_.*\\.yml$"
       recursive: false
       include_start_directory: true
       fields:
         - title
         - description
   store_fields:
     directory: sourceDirectory
     filename: sourceFilename
     root: sourceRoot

Defaults preserve existing behaviour:

* Omit ``recursive`` (or set ``false``) for flat globs only. ``**`` is
  meaningful only when ``recursive: true``.
* Omit ``fields`` for a full-document ``json_normalize``.
* Omit ``include_start_directory`` (or set ``true``) to keep matches in
  the source directory itself. Set ``false`` for descendants only.
* Field projection applies to **mapping-valued** readers. Non-mapping
  payloads warn and yield nulls for the listed fields.
* Path confinement (allowed roots) still applies to every matched path.

Nested catalog example:

.. code-block:: yaml

   type: yaml_directory
   source:
     - directory: catalogs
       glob: "**/config.yml"
       recursive: true
   fields:
     - title
     - description
     - date
   store_fields:
     directory: sourceDirectory
     filename: sourceFilename
     root: sourceRoot

To present directory rows as one wide data point instead of a multi-row
table, wrap the directory source in ``wide_flatten``. See the README
``wide_flatten`` section.
