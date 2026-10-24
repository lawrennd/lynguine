# Changelog

All notable user-facing changes to lynguine are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] — 2026-10-24

Snapshot of the document, access, and confinement work that has been on
`main` since 0.1.1 (PyPI, 6 July 2024). This is not a claim that every CIP
is closed. Several slices remain follow-on and are listed below.

Documentation: [Read the Docs](https://lynguine.readthedocs.io/en/latest/)
and [GitHub Pages](https://lawrennd.github.io/lynguine/).

### Breaking

- **Configured paths are confined to allowed roots** ([CIP-000A](cip/cip000A.md)).
  `Interface.from_file`, `SessionManager.create_session`, and access-stage
  filenames from interface YAML resolve under `allowed_roots`. The default
  root is the interface directory (the directory already used to join
  files). Absolute paths *outside* that directory — for example
  `/tmp/foo.yml` named from a project interface — now raise
  `lynguine.access.paths.PathEscapeError` unless you add that root or opt
  out.

  Opt-out is explicit: pass `allowed_roots=None` or `unbounded_paths=True`
  at the flow entry point. YAML `allowed_roots` cannot enlarge the jail.
  Primitive helpers such as `read_yaml_file("/Users/me/data.yml")` are
  unchanged; they remain trusted-caller APIs.

  `inherit.directory` is a trusted config mechanism: the inherit directory
  and the parent’s roots are unioned into the child. Relative inherited
  `filename` specs bind to `inherit.directory`. Paths that appear only
  inside YAML and sit outside those roots still raise `PathEscapeError`.
  HTTP / `from_cwd_file` inherit outside the process CWD still PathEscapes.

- **NumPy 2** is now required (`numpy >= 2.0.0`). 0.1.1 pinned
  `numpy >= 1.0.0,< 2.0.0`.

Python remains `>= 3.11,< 4.0`, as in 0.1.1.

### Added

- Optional **`documents` extra** (`pymupdf`, `python-docx`): pluggable PDF,
  DOCX, Markdown, and YAML form-field readers with layout strategies and
  `document_segment` ([CIP-0013](cip/cip0013.md)). Strategies on `main`
  include `pub_dialogue.v1`, DOCX dialogue strategies, academic references,
  `cam_panel_application.v1`, and `socratic_markdown.v1`.
  Install with `pip install 'lynguine[documents]'`.

- Optional **`parquet` extra** (`pyarrow >= 19,< 27`): named stores with
  `type: parquet` ([CIP-0015](cip/cip0015.md)).
  Install with `pip install 'lynguine[parquet]'`.

- **Gzip YAML/JSON stores** without changing logical `type: yaml` /
  `type: json`. Compression is declared by suffix (`.yml.gz`, `.json.gz`)
  and/or `compress: gzip`. `store_stat` reports path, exists, mtime, size,
  and codec without loading the table ([CIP-0015](cip/cip0015.md)).

- **Explode and pack** as Access IO: explode a list field to one row per
  item; pack selected columns into one corpus row of aligned array fields
  ([CIP-0014](cip/cip0014.md)). Packed YAML writes omit embeddings while
  pack still sees them.

- **`wide_flatten`**: many tall rows to one wide row whose column names
  incorporate the former index values. Outer `index` is the singleton
  result label (wrapping index). Writable scores stay on the tall store;
  wide names are a view unless the flow explicitly unflattens
  ([CIP-0010](cip/cip0010.md)).

- **Recursive directory discovery and field projection** for YAML (and
  sibling directory types): `**/` globs walk nested trees; each file can
  contribute an explicit field projection instead of a full
  `json_normalize`. `include_start_directory` supports descendants-only
  discovery ([CIP-000F](cip/cip000F.md)).

- **Encrypted credential storage** for API keys and similar secrets
  (AES-256 at rest, multiple backends, audit logging)
  ([CIP-0005](cip/cip0005.md)). Credential identifiers in logs are hashed
  rather than written in the clear ([CIP-000B](cip/cip000B.md)). See the
  [security guide](https://lynguine.readthedocs.io/en/latest/security/).

### Changed

- **Join overlap is earlier-wins.** `hstack` and `CustomDataFrame.to_pandas()`
  no longer raise pandas `columns overlap` / `MergeError` when later
  sources share a name (including a third source recreating `col_right`).
  Later colliding columns are dropped. Two-way overlap still suffixes the
  right copy when `rsuffix` is set
  ([CIP-000E](cip/cip000E.md); [stacking docs](https://lawrennd.github.io/lynguine/getting_started/stacking.html)).

- **Liquid mapping is demand-driven.** `liquid_to_value` fetches only the
  identifiers the template names. `mapping()` with no arguments still
  returns the full-row dict. Debug logs do not stringify cell values
  ([CIP-0016](cip/cip0016.md)).

- GitPython is pinned `>= 3.2.1` (Dependabot; was an open pip CVE on 3.1.x).
- `cryptography >= 50.0.0`.

### Fixed

- `wide_flatten` restores wrapping `index` after finalize so singleton
  frames load (`Missing index field` on referia root overview configs)
  ([PR #33](https://github.com/lawrennd/lynguine/pull/33)).
- Inherited data paths bind a missing or relative `directory` to
  `inherit.directory` so parent files are not resolved against the child
  ([PR #56](https://github.com/lawrennd/lynguine/pull/56)).
- `save_flows` no longer writes an unnamed index as CSV column 0
  ([PR #44](https://github.com/lawrennd/lynguine/pull/44)).
- `CustomDataFrame.at` no longer writes cache values into an empty output
  ([PR #42](https://github.com/lawrennd/lynguine/pull/42)).
- Nested YAML constants load as a single row
  ([PR #34](https://github.com/lawrennd/lynguine/pull/34)).

### Documentation

- Getting-started pages for stacking/joins, directory sources, and column
  management, compressed from closed CIPs.
- Read the Docs install uses current Poetry build jobs (the old
  `python.install.method: poetry` keys were removed upstream).
- GitHub Actions publishes to PyPI when a GitHub Release is published
  with tag `vX.Y.Z` matching `poetry version`.

### Known limitations

These ship with 0.1.2 rather than blocking it:

- CIP-0013 is still In Progress: example flow YAML is missing; OCR is an
  explicit follow-on.
- CIP-0014 is still In Progress: `file_catalog` helper and explode/pack
  edge cases (empty pack, inherit skip, explode-then-pack, parameter nulls).
- CIP-0015’s gzip/parquet checklist is complete; the CIP status field is
  still In Progress.
- `from_flow` still hardcodes `strict_columns=False`.
- CIP-000A CodeQL dismissals for remaining primitive `open()` alerts live
  on [CIP-000D](cip/cip000D.md) and are not closed.
- LLM extraction remains in referia ([CIP-0004](cip/cip0004.md) is
  Proposed).

### Upgrade

```bash
pip install -U 'lynguine[documents,parquet]'
```

Omit the extras if you do not need PDF/DOCX readers or parquet stores.
If a flow names files outside the interface directory, add that directory
to the caller’s `allowed_roots`, use `inherit.directory` for parent
configs, or pass `unbounded_paths=True` at the trusted local entry point.

## [0.1.1] — 2024-07-06

First release on PyPI.
