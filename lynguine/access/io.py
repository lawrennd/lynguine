"""Access-stage I/O for lynguine.

Flow-level readers (``read_data``, ``write_data``, directory globs) confine
configured paths with ``extract_full_filename`` / ``confine_configured_path``
before calling into file helpers (CIP-000A).

The filename helpers below (``read_yaml_file``, ``read_json_file``, and the
other ``*_file`` functions) are trusted-caller primitives: they ``open()``
the path they are given and do not apply ``allowed_roots``. Untrusted or
config-supplied names must be confined at the flow boundary first, not
passed in raw from HTTP or interface YAML. CodeQL ``py/path-injection``
on those ``open()`` sites is a trusted-caller primitive, not a missing
jail (CIP-000D cluster A).
"""
import os
import glob
import gzip
from contextlib import contextmanager
from datetime import datetime


import sys
import re
import tempfile

import yaml
import json

import numpy as np
import pandas as pd

import frontmatter
import pypandoc

import bibtexparser as bp

from ..util.misc import (
    extract_full_filename,
    extract_root_directory,
    extract_file_type,
    get_path_env,
    remove_nan,
    reorder_dictionary,
    prompt_stdin,
)
from .paths import confine_configured_path
from ..util.fake import Generate
from ..assess.compute import Compute
from ..config.context import Context
from ..util.dataframe import reorder_dataframe
from ..log import Logger

from ..config.interface import Interface

GSPREAD_AVAILABLE = True
try:
    import gspread_pandas as gspd
except ImportError:
    GSPREAD_AVAILABLE = False

# Import secure credential management
try:
    from ..security.credentials import (
        get_credential_manager,
        CredentialNotFoundError,
        CredentialValidationError
    )
    from ..security.access_control import (
        get_access_controller,
        AccessLevel,
        AccessDeniedError,
        RateLimitError
    )
    from ..security.secure_logging import redact_credential_identifier
    SECURE_CREDENTIALS_AVAILABLE = True
except ImportError:
    SECURE_CREDENTIALS_AVAILABLE = False

# This file accesses the data

"""Place commands in this file to access the data electronically. Don't remove any missing values, or deal with outliers. Make sure you have legalities correct, both intellectual property and personal data privacy rights. Beyond the legal side also think about the ethical issues around this data. """

ctxt = Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)

GZIP_MAGIC = b"\x1f\x8b"
_GZIP_SUFFIXES = (".gz", ".gzip")


def _compress_kwargs(details, write=True) -> dict:
    """Pass compress arguments only when the store declares them."""
    kwargs = {}
    compress = details.get("compress") if isinstance(details, dict) else None
    if compress is not None:
        kwargs["compress"] = compress
    if write and isinstance(details, dict) and "compress_level" in details:
        kwargs["compress_level"] = details["compress_level"]
    return kwargs


def gzip_codec_from_name(filename: str) -> str | None:
    """Return ``gzip`` if *filename* declares compression by suffix."""
    lower = str(filename).lower()
    return "gzip" if lower.endswith(_GZIP_SUFFIXES) else None


def resolve_text_codec(filename: str, compress=None) -> str | None:
    """Declare gzip from suffix and/or ``compress: gzip`` (CIP-0015).

    A ``.yml`` name is never treated as gzip. ``compress: gzip`` with a
    non-``.gz`` filename is an error.
    """
    by_name = gzip_codec_from_name(filename)
    if compress not in (None, "gzip"):
        errmsg = f'Unknown compress codec "{compress}".'
        log.error(errmsg)
        raise ValueError(errmsg)
    if compress == "gzip" and not by_name:
        errmsg = f'compress: gzip requires a .gz filename, got "{filename}".'
        log.error(errmsg)
        raise ValueError(errmsg)
    return by_name


def _raise_if_undeclared_gzip(filename: str, compress=None) -> None:
    """Fail if a non-``.gz`` path contains gzip bytes (no magic sniffing to decode)."""
    if resolve_text_codec(filename, compress) == "gzip":
        return
    if not os.path.isfile(filename):
        return
    with open(filename, "rb") as fh:
        head = fh.read(2)
    if head == GZIP_MAGIC:
        errmsg = (
            f'File "{filename}" is gzip-compressed but the name does not '
            "end in .gz; rename to .yml.gz / .json.gz or write uncompressed YAML."
        )
        log.error(errmsg)
        raise ValueError(errmsg)


@contextmanager
def open_text_store(filename, mode, compress=None, compress_level=6):
    """Open a YAML/JSON store as text, optionally gzip-wrapped."""
    codec = resolve_text_codec(filename, compress)
    if codec == "gzip":
        gz_mode = mode if "t" in mode else f"{mode}t"
        with gzip.open(
            filename,
            gz_mode,
            encoding="utf-8",
            compresslevel=compress_level,
        ) as stream:
            yield stream
    else:
        with open(filename, mode) as stream:
            yield stream


_PYARROW_INSTALL = (
    "pyarrow is required for parquet stores. "
    "Install with: pip install 'lynguine[parquet]' "
    "or: poetry install --extras parquet"
)
_PARQUET_COMPRESS = {
    "snappy",
    "zstd",
    "gzip",
    "brotli",
    "lz4",
    "none",
    "uncompressed",
}


class PyArrowMissingError(ImportError):
    """Raised when parquet IO is requested but pyarrow is not installed."""


def _import_pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise PyArrowMissingError(_PYARROW_INSTALL) from exc
    return pa, pq


def _parquet_compression(details) -> str:
    """Parquet column codec (CIP-0015 phase 2). Default snappy."""
    compress = details.get("compress") if isinstance(details, dict) else None
    if compress is None:
        return "snappy"
    key = str(compress).lower()
    if key not in _PARQUET_COMPRESS:
        errmsg = f'Unknown parquet compress codec "{compress}".'
        log.error(errmsg)
        raise ValueError(errmsg)
    if key in {"none", "uncompressed"}:
        return "none"
    return key


def _cell_as_nested_list(value):
    """Python lists of floats/strings for Arrow list columns (not pickle)."""
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        return [_cell_as_nested_list(item) for item in value]
    if isinstance(value, (np.floating, np.integer)):
        if pd.isna(value):
            return None
        return float(value) if isinstance(value, np.floating) else int(value)
    if isinstance(value, float) and pd.isna(value):
        return None
    return value


def _arrow_list_type(value, pa):
    """Infer Arrow list type for a sample cell, or None if not a list."""
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if not isinstance(value, (list, tuple)):
        return None
    if len(value) == 0:
        return None
    inner = value[0]
    if isinstance(inner, np.ndarray):
        inner = inner.tolist()
    if isinstance(inner, (list, tuple)):
        if inner and isinstance(inner[0], (int, float, np.floating, np.integer)):
            return pa.list_(pa.list_(pa.float32()))
        return None
    if isinstance(inner, (int, float, np.floating, np.integer)):
        return pa.list_(pa.float32())
    if isinstance(inner, str):
        return pa.list_(pa.string())
    return None


def _list_column_arrow_types(df, details, pa) -> dict:
    """Numeric/string list columns as Arrow lists, not object/pickle."""
    types = {}
    declared = details.get("list_columns") if isinstance(details, dict) else None
    if isinstance(declared, dict):
        for col in declared:
            if col in df.columns:
                types[col] = pa.list_(pa.float32())
    elif isinstance(declared, list):
        for col in declared:
            if col in df.columns:
                types[col] = pa.list_(pa.float32())
    for col in df.columns:
        if col in types:
            continue
        sample = df[col].dropna()
        if len(sample) == 0:
            continue
        inferred = _arrow_list_type(sample.iloc[0], pa)
        if inferred is not None:
            types[col] = inferred
    return types


def _dataframe_to_arrow_table(df, details, pa):
    """Build a pyarrow Table with list<float32> embedding columns."""
    frame = _as_pandas(df).copy()
    idx_name = frame.index.name
    if idx_name and idx_name not in frame.columns:
        frame = frame.reset_index()
    list_types = _list_column_arrow_types(frame, details, pa)
    arrays = []
    names = []
    for col in frame.columns:
        names.append(str(col))
        if col in list_types:
            arrays.append(
                pa.array(
                    [_cell_as_nested_list(v) for v in frame[col].tolist()],
                    type=list_types[col],
                )
            )
        else:
            arrays.append(pa.array(frame[col]))
    return pa.Table.from_arrays(arrays, names=names)


def _cell_from_arrow(value):
    """Normalise parquet list cells to Python lists of float/str."""
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.dtype == object:
            return [_cell_from_arrow(item) for item in value.tolist()]
        return [_cell_from_arrow(item) for item in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_cell_from_arrow(item) for item in value]
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def _python_lists_from_parquet(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        sample = out[col].dropna()
        if len(sample) == 0:
            continue
        first = sample.iloc[0]
        if isinstance(first, (list, tuple, np.ndarray)):
            out[col] = [_cell_from_arrow(v) for v in out[col].tolist()]
    return out


def parquet_codec_from_file(filename: str) -> str | None:
    """Column codec from parquet metadata without loading the table."""
    _pa, pq = _import_pyarrow()
    meta = pq.read_metadata(filename)
    codecs = set()
    for i in range(meta.num_row_groups):
        group = meta.row_group(i)
        for j in range(group.num_columns):
            codecs.add(str(group.column(j).compression).lower())
    if not codecs:
        return None
    if len(codecs) == 1:
        return next(iter(codecs))
    return ",".join(sorted(codecs))


def multiline_str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# Custom dumper that forces block scalars for multiline strings
class LynguineSafeDumper(yaml.SafeDumper):
    def choose_scalar_style(self):
        """Override to force block scalar style for multiline strings."""
        # Call parent to get initial style choice
        if self.event.style:
            self.event.style = self.event.style
        else:
            # Default from parent
            if (not self.simple_key_context and
                (self.flow_level and self.event.value in '[]{}:,')):
                self.event.style = "'"
            
        # Force block literal style for multiline strings
        if '\n' in self.event.value and self.event.style == '|':
            # Keep the block scalar style that was requested
            return self.event.style
        
        return super().choose_scalar_style()

# Register the representer with our custom dumper
LynguineSafeDumper.add_representer(str, multiline_str_representer)

# class EnvTag(yaml.YAMLObject):
#     yaml_tag = u'!ENV'

#     def __init__(self, env_var):
#         self.env_var = env_var

#     def __repr__(self):
#         v = os.environ.get(self.env_var) or ''
#         return 'EnvTag({}, contains={})'.format(self.env_var, v)

#     @classmethod
#     def from_yaml(cls, loader, node):
#         return EnvTag(node.value)

#     @classmethod
#     def to_yaml(cls, dumper, data):
#         value = dumper.represent_scalar(cls.yaml_tag, data.env_var)
#         if '\n' in value:
#             # Use the '|' style for multi-line strings
#             return dumper.represent_scalar(cls.yaml_tag, value, style="|")
#         else:
#             return dumper.represent_scalar(cls.yaml_tag, value)
#         return value


# Required for safe_load
# yaml.SafeLoader.add_constructor('!ENV', EnvTag.from_yaml)
# Required for safe_dump
# yaml.SafeDumper.add_multi_representer(EnvTag, EnvTag.to_yaml)

bibtex_sort_by = ["author", "year", "title"]
bibtex_column_order = [
    "ENTRYTYPE",
    "ID",
    "title",
    "author",
    "editor",
    "abstract",
    "year",
    "journal",
    "booktitle",
    "volume",
    "issue",
    "pages",
    "publisher",
    "address",
    "doi",
    "url",
    "note",
]


def str_type():
    return str


def bool_type():
    return pd.BooleanDtype()


def int_type():
    return pd.Int32Dtype()


def float_type():
    return pd.Float64Dtype()


def extract_dtypes(details):
    """
    Extract dtypes from directory.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The dtypes.
    :rtype: dict
    """
    dtypes = {}
    if "dtypes" in details:
        if details["dtypes"] is not None:
            for dtype in details["dtypes"]:
                dtypes[dtype["field"]] = globals()[dtype["type"]]()
    return dtypes


def extract_sheet(details, gsheet=True):
    """
    Extract the sheet name from details

    :param details: The details of the file to be read.
    :type details: dict
    :param gsheet: Whether to use gspread_pandas.
    :type gsheet: bool
    """
    if "sheet" in details:
        return details["sheet"]
    else:
        if gsheet:
            return 0
        else:
            return None


def _get_google_sheets_config(details):
    """
    Get Google Sheets configuration using secure credential management.
    
    This function retrieves Google Sheets credentials securely, falling back
    to the legacy context-based approach if secure credentials are not available.
    
    :param details: The details dictionary that may contain credential references
    :type details: dict
    :return: Configuration dictionary for gspread_pandas
    :rtype: dict
    :raises ValueError: If credentials cannot be retrieved
    """
    gconfig = {}
    
    # Try secure credential management first
    if SECURE_CREDENTIALS_AVAILABLE:
        try:
            # Get access controller for authorization
            access_controller = get_access_controller()
            
            # Determine which credential to use
            credential_key = None
            if "credential" in details:
                # Explicit credential reference in details
                credential_key = details["credential"]
            elif "google_oauth" in ctxt:
                # Check if context has a credential reference
                oauth_config = ctxt["google_oauth"]
                if isinstance(oauth_config, str) and oauth_config.startswith("${credential:"):
                    # Extract credential key from reference
                    credential_key = oauth_config[13:-1]  # Remove ${credential: and }
            else:
                # Default credential keys
                credential_key = "google_sheets_oauth"
            
            if credential_key:
                # Authorize access
                try:
                    access_controller.authorize_access(
                        credential_key=credential_key,
                        operation=AccessLevel.READ,
                        context="google_sheets_read"
                    )
                except (AccessDeniedError, RateLimitError):
                    log.error(
                        "Access denied for Google Sheets credential "
                        f"{redact_credential_identifier(credential_key)}"
                    )
                    raise ValueError("Failed to authorize credential access")
                
                # Get credential from manager
                credential_manager = get_credential_manager()
                try:
                    credential = credential_manager.get_credential(
                        credential_key,
                        credential_type="google_oauth"
                    )
                    
                    if credential and "value" in credential:
                        cred_value = credential["value"]
                        if isinstance(cred_value, dict):
                            # Expand environment variables in credential values
                            for key, val in cred_value.items():
                                if isinstance(val, str):
                                    gconfig[key] = os.path.expandvars(val)
                                else:
                                    gconfig[key] = val
                            
                            log.debug("Using secure credential management for Google Sheets")
                            return gconfig
                except CredentialNotFoundError:
                    safe_credential_key = redact_credential_identifier(credential_key)
                    log.warning(
                        f"Credential '{safe_credential_key}' not found in secure storage, "
                        "falling back to context-based credentials"
                    )
                except CredentialValidationError as e:
                    log.warning(
                        f"Credential validation failed: {e}, "
                        "falling back to context-based credentials"
                    )
        except Exception as e:
            log.warning(
                f"Error using secure credential management: {e}, "
                "falling back to context-based credentials"
            )
    
    # Fallback to legacy context-based approach
    if "google_oauth" in ctxt:
        log.debug("Using legacy context-based credentials for Google Sheets")
        for key, val in ctxt["google_oauth"].items():
            if isinstance(val, str):
                gconfig[key] = os.path.expandvars(val)
            else:
                gconfig[key] = val
        return gconfig
    elif "gspread_pandas" in ctxt:
        log.debug("Using legacy gspread_pandas context-based credentials")
        for key, val in ctxt["gspread_pandas"].items():
            if isinstance(val, str):
                gconfig[key] = os.path.expandvars(val)
            else:
                gconfig[key] = val
        return gconfig
    else:
        errmsg = (
            "No Google Sheets credentials found. "
            "Configure credentials using secure credential management or "
            "add 'google_oauth' to your context configuration."
        )
        log.error(errmsg)
        raise ValueError(errmsg)


def read_json(details):
    """
    Read data from a json file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    filename = extract_full_filename(details)
    data = read_json_file(filename, **_compress_kwargs(details, write=False))
    return pd.DataFrame(data)


def write_json(df, details):
    """
    Write data to a json file.

    :param df: The data to be written.

    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    write_json_file(df.to_dict("records"), filename, **_compress_kwargs(details))


def _dig_mapping_path(mapping, path):
    """Return ``mapping`` value at a dotted path, or ``None`` if missing."""
    current = mapping
    for part in str(path).split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _project_yaml_document_fields(data, fields):
    """Project a YAML document mapping to flat columns for constants use.

    ``fields`` entries may be:

    - a string top-level key or dotted path (``ghub.repository``);
    - a mapping with ``field`` and either ``path`` (dotted dig) or
      ``liquid`` (template rendered against the document as context).
    """
    if not isinstance(fields, list):
        raise ValueError(
            f'"fields" for yaml document projection must be a list, got {type(fields).__name__}.'
        )

    projected = {}
    liquid_env = None
    for entry in fields:
        if isinstance(entry, str):
            if "." in entry:
                projected[entry] = _dig_mapping_path(data, entry)
            else:
                projected[entry] = data.get(entry)
            continue
        if isinstance(entry, dict):
            if "field" not in entry:
                raise ValueError(
                    'Each mapping in yaml "fields" must include a "field" name.'
                )
            name = entry["field"]
            if "liquid" in entry:
                if liquid_env is None:
                    import liquid as lq

                    liquid_env = lq.Environment(tolerance=lq.Mode.LAX)
                projected[name] = liquid_env.from_string(entry["liquid"]).render(**data)
            elif "path" in entry:
                projected[name] = _dig_mapping_path(data, entry["path"])
            else:
                projected[name] = data.get(name)
            continue
        raise ValueError(
            f'Unsupported yaml "fields" entry type {type(entry).__name__}; '
            "expected str or mapping."
        )
    return projected


def _yaml_mapping_to_frame(data, details):
    """Load a YAML mapping as a single-row DataFrame (constants / parameters)."""
    if "fields" in details and details["fields"] is not None:
        data = _project_yaml_document_fields(data, details["fields"])

    if all(not isinstance(v, (list, dict)) for v in data.values()):
        index_name = details.get("index", "value")
        return pd.DataFrame(data, index=[index_name])

    # Nested values remain as cell objects (same pattern as read_markdown).
    return pd.DataFrame([data])


def read_yaml(details):
    """
    Read data from a yaml file.

    A top-level YAML mapping is always treated as a **single-row** table
    (constants / parameters). All-scalar maps keep an explicit index
    (default ``value``). Maps with nested dict/list values become one row
    with those values as cell objects, matching ``read_markdown``.

    Optional ``fields`` projects the document before the row is formed
    (top-level keys, dotted paths, or ``field`` + ``path`` / ``liquid``).

    A YAML sequence of mappings remains a multi-row table.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    :raises ValueError: If the document is neither a mapping nor a sequence.
    """
    filename = extract_full_filename(details)
    data = read_yaml_file(filename, **_compress_kwargs(details, write=False))

    if isinstance(data, dict):
        return _yaml_mapping_to_frame(data, details)

    if isinstance(data, list):
        return pd.DataFrame(data)

    raise ValueError(
        f'YAML file "{filename}" must contain a mapping or a sequence of '
        f"mappings for tabular load; got {type(data).__name__}."
    )

def read_markdown(details):
    """
    Read data from a markdown file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    filename = extract_full_filename(details)
    data = read_markdown_file(filename)
    return pd.DataFrame([data])

def write_markdown(df, details):
    """
    Write data to a markdown file.

    :param df: The data to be written.
    :type df: pandas.DataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    data_dict = df.to_dict("records")

    # Remove all the nan and missing values from the dictionary.
    for num, entry in enumerate(data_dict):
        data_dict[num] = remove_nan(entry)

    write_markdown_file(data_dict, filename)

def write_yaml(df, details):
    """
    Write data to a yaml file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    data_dict = df.to_dict("records")

    keep_nulls = bool(details.get("keep_nulls"))
    for num, entry in enumerate(data_dict):
        if keep_nulls:
            cleaned = {}
            for key, val in entry.items():
                if isinstance(val, float) and pd.isna(val):
                    cleaned[key] = None
                else:
                    cleaned[key] = val
            data_dict[num] = cleaned
        else:
            data_dict[num] = remove_nan(entry)
    write_yaml_file(data_dict, filename, **_compress_kwargs(details))


def read_bibtex(details):
    """
    Read data from a bibtex file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    filename = extract_full_filename(details)
    data = read_bibtex_file(filename)

    return (
        reorder_dataframe(pd.DataFrame(data), bibtex_column_order)
        .sort_values(by=bibtex_sort_by)
        .reset_index(drop=True), details
    )


def write_bibtex(df, details):
    """
    Write data to a bibtex file.

    :param df: The data to be written.
    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    data_dict = df.to_dict("records")

    # Remove all the nan and missing values from the dictionary.
    for num, entry in enumerate(data_dict):
        data_dict[num] = remove_nan(entry)

    write_bibtex_file(data_dict, filename)


def read_directory(
    details, filereader=None, filereader_args={}, default_glob="*", source=None
):
    """
    Read data from a directory of files.

    Opt-in ``recursive: true`` on a source entry (or on ``details``) enables
    ``glob.glob(..., recursive=True)`` so patterns such as ``**/*.yml`` walk
    nested trees. Default is non-recursive; ``**`` is only meaningful when
    ``recursive`` is true (CIP-000F).

    Opt-in ``fields`` on a source entry (or on ``details``) projects each
    mapping-valued file to the listed top-level keys before normalize
    (CIP-000F). Absent ``fields`` keeps full-document behaviour.

    ``include_start_directory`` (source entry or ``details``, default
    ``True``) controls whether matches whose immediate parent is the source
    ``directory`` itself are kept. Set ``False`` for descendants-only
    discovery (e.g. nested ``**/_referia.yml`` without the file in ``.``).

    :param details: The details of the directory to be read.
    :type details: dict
    :param filereader: The function to be used to read the file.
    :type filereader: function
    :param filereader_args: The arguments to be passed to the filereader.
    :type filereader_args: dict
    :param default_glob: The default glob to be used if none is specified.
    :type default_glob: str
    :param source: The source information for the data.
    :type source: dict
    :raises ValueError: if the same filename is specified multiple times.
    """
    # Batches of (confined paths, fields) so per-source field lists apply.
    batches = []
    if "source" in details:
        sources = details["source"]
        if type(sources) is not list:
            sources = [sources]

        for source in sources:
            if "glob" in source:
                glob_text = source["glob"]
            else:
                glob_text = default_glob

            if "directory" in source:
                directory = os.path.expandvars(source["directory"])
                # Make relative paths relative to base_directory if specified
                if not os.path.isabs(directory) and "base_directory" in details:
                    directory = os.path.join(details["base_directory"], directory)
                directory = confine_configured_path(directory, details)
            else:
                directory = "."
            # Source entry wins; else top-level details; default false.
            recursive = bool(source.get("recursive", details.get("recursive", False)))
            include_start_directory = source.get(
                "include_start_directory",
                details.get("include_start_directory", True),
            )
            if "fields" in source:
                fields = source["fields"]
            else:
                fields = details.get("fields")
            globname = os.path.join(
                directory,
                glob_text,
            )
            # glob.glob already returns paths that include the directory prefix;
            # do not rejoin directory onto matches (relative dirs double-joined).
            newfiles = glob.glob(globname, recursive=recursive)
            log.debug(
                f'Reading directory "{globname}" recursive={recursive} '
                f"include_start_directory={include_start_directory} "
                f"matches={len(newfiles)}"
            )
            if len(newfiles) == 0:
                log.warning(f'No files match "{globname}"')
            if "regexp" in source:
                regexp = source["regexp"]
                addfiles = [
                    filename
                    for filename in newfiles
                    if re.match(regexp, os.path.basename(filename))
                ]
                if len(addfiles) == 0:
                    log.warning(f'No files match "regexp"')
            else:
                addfiles = newfiles
            if include_start_directory is False:
                start_dir = os.path.realpath(directory)
                addfiles = [
                    filename
                    for filename in addfiles
                    if os.path.realpath(os.path.dirname(filename)) != start_dir
                ]
            if addfiles:
                confined = [
                    confine_configured_path(filename, details)
                    for filename in addfiles
                ]
                batches.append((confined, fields))
        if len(batches) == 0:
            log.warning(f'No files in "{sources}".')
    else:
        log.warning(f'No source in "{details}".')

    all_files = [filename for files, _fields in batches for filename in files]
    if len(all_files) != len(set(all_files)):
        errmsg = "There are repeated files listed in the file list."
        log.error(errmsg)
        raise ValueError(errmsg)

    frames = []
    for filelist, fields in batches:
        frames.append(
            read_files(
                filelist,
                details["store_fields"],
                filereader,
                filereader_args,
                fields=fields,
            )
        )
    if not frames:
        return pd.DataFrame()
    if len(frames) == 1:
        return frames[0]
    return pd.concat(frames, ignore_index=True)


def read_list(filelist):
    """
    Read from a list of files.

    Trusted-caller API: entries in ``filelist`` are not confined here.
    Directory-glob flow paths confine before calling ``read_files``.

    :param filelist: The list of files to be read.
    :type filelist: list
    :return: The data read from the files.
    :rtype: pandas.DataFrame
    """
    return read_files(filelist)


def _project_mapping_fields(payload, fields, filename):
    """Keep only listed top-level keys from a mapping-valued file payload.

    Non-mapping payloads warn and become nulls for each listed field so
    path ``store_fields`` can still be attached without crashing (CIP-000F).
    """
    if not isinstance(payload, dict):
        log.warning(
            f'Fields projection for "{filename}" received '
            f"{type(payload).__name__}, not a mapping; listed fields will be null."
        )
        return {key: None for key in fields}
    return {key: payload.get(key) for key in fields}


def read_files(
    filelist, store_fields=None, filereader=None, filereader_args=None, fields=None
):
    """
    Read files from a given list.

    Trusted-caller API: this function does not apply ``allowed_roots``.
    Callers that have configuration or request-derived names must confine
    each path first (CIP-000A).

    When ``fields`` is set, each mapping-valued payload is reduced to those
    top-level keys before path ``store_fields`` are appended (CIP-000F).

    :param filelist: The list of files to be read.
    :type filelist: list
    :param store_fields: The fields to be stored in the data.
    :type store_fields: dict
    :param filereader: The function to be used to read the file.
    :type filereader: function
    :param filereader_args: The arguments to be passed to the filereader.
    :type filereader_args: dict
    :param fields: Optional list of top-level keys to keep from each mapping.
    :type fields: list or None
    :return: The data read from the files.
    :rtype: pandas.DataFrame
    """
    if store_fields is not None:
        directory_field = store_fields["directory"]
        filename_field = store_fields["filename"]
        root_field = store_fields["root"]
    else:
        directory_field = "sourceDirectory"
        filename_field = "sourceFile"
        root_field = "sourceRoot"

    if len(filelist) != len(set(filelist)):
        errmsg = "There are repeated files listed in the file list."
        log.error(errmsg)
        raise ValueError(errmsg)
    filelist = sorted(filelist)
    data = []
    for filename in filelist:
        if not os.path.exists(filename):
            log.warning(f'File "{filename}" is not a file or a directory.')
        # Determine reader for each file (use provided filereader or detect from file type)
        if filereader is None:
            typ = extract_file_type(filename)
            current_reader = default_file_reader(typ)
        else:
            current_reader = filereader
        if filereader_args is None:
            payload = current_reader(filename)
        else:
            payload = current_reader(filename, **filereader_args)
        if fields is not None:
            payload = _project_mapping_fields(payload, fields, filename)
        data.append(payload)

        # Add the root location, directory and filename to the data.
        split_path = os.path.split(filename)
        root, direc = extract_root_directory(split_path[0])
        if root_field in data[-1]:
            raise ValueError(
                f'The field "{root_field}" is already in the data and is registered for setting as the root field.'
            )
        data[-1][root_field] = root
        if directory_field in data[-1]:
            raise ValueError(
                f'The field "{directory_field}" is already in the data and is registered for setting as the directory field.'
            )
        data[-1][directory_field] = direc
        if filename_field in data[-1]:
            raise ValueError(
                f'The field "{filename_field}" is already in the data and is registered for setting as the filename field.'
            )
        data[-1][filename_field] = split_path[1]
    return pd.json_normalize(data)


def write_directory(df, details, filewriter=None, filewriter_args={}):
    """
    Write scoring data to a directory of files.

    :param df: The data to be written.
    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    :param filewriter: The function to be used to write the file.
    :type filewriter: function
    :param filewriter_args: The arguments to be passed to the filewriter.
    :type filewriter_args: dict
    :raises ValueError: if the same filename is specified multiple times.
    """
    filename_field = details["store_fields"]["filename"]
    directory_field = details["store_fields"]["directory"]
    root_field = details["store_fields"]["root"]

    filenames = []
    # Check that none of the filenames are the same.
    for index, row in df.iterrows():
        # Don't write a file that contains only nulls
        if not row.isnull().values.all():
            directoryname = os.path.expandvars(
                os.path.join(
                    row[root_field],
                    row[directory_field],
                )
            )
            # Make relative paths relative to base_directory if specified
            if not os.path.isabs(directoryname) and "base_directory" in details:
                directoryname = os.path.join(details["base_directory"], directoryname)

            fullfilename = confine_configured_path(
                os.path.join(directoryname, row[filename_field]), details
            )
            directoryname = os.path.dirname(fullfilename)
            if not os.path.exists(directoryname):
                os.makedirs(directoryname)
            if fullfilename in filenames:
                raise ValueError(
                    'The specified filed name "{fullfilename}" has already been used for a different row of the data.'
                )
            filenames.append(fullfilename)
            if filewriter is None:
                typ = extract_file_type(fullfilename)
                filewriter = default_file_writer(typ)

            row_dict = row.to_dict()
            row_dict = remove_nan(row_dict)
            # Don't save the file information because that's situational.
            del row_dict[filename_field]
            del row_dict[root_field]
            del row_dict[directory_field]
            if filewriter_args is None:
                filewriter(row_dict, fullfilename)
            else:
                filewriter(row_dict, fullfilename, **filewriter_args)


def read_json_file(filename, compress=None):
    """
    Read a json file and return a python dictionary.

    Trusted-caller I/O: does not confine ``filename``. Configured or
    untrusted names must go through ``extract_full_filename`` first (CIP-000A).

    :param filename: The filename of the json file.
    :type filename: str
    :param compress: Optional ``gzip``; suffix ``.json.gz`` also selects gzip.
    :return: The data read from the file.
    :rtype: dict
    """
    _raise_if_undeclared_gzip(filename, compress)
    with open_text_store(filename, "r", compress=compress) as stream:
        try:
            log.debug(f'Reading json file "{filename}"')
            data = json.load(stream)
        except json.JSONDecodeError as vis:
            log.warning(vis)
            data = {}
    return data


def write_json_file(data, filename, compress=None, compress_level=6):
    """Write a json file from a python dictionary.

    Trusted-caller I/O: does not confine ``filename`` (CIP-000A).
    """
    with open_text_store(
        filename, "w", compress=compress, compress_level=compress_level
    ) as stream:
        try:
            log.debug(f'Writing json file "{filename}".')
            json.dump(data, stream)
        except json.JSONDecodeError as vis:
            log.warning(vis)


def read_txt_file(filename):
    """Read a text file and return a dictionary with the content.

    Trusted-caller I/O: does not confine ``filename`` (CIP-000A).
    """
    with open(filename, 'r') as f:
        content = f.read()
    return {"content": content}


def default_file_reader(typ):
    """
    Return the default file reader for a given type.

    :param typ: The type of file to be read.
    :type typ: str
    :return: The default file reader.
    :rtype: function
    :raises ValueError: if the type is not recognised.
    """
    if typ == "markdown":
        return read_markdown_file
    if typ == "yaml":
        return read_yaml_file
    if typ == "json":
        return read_json_file
    if typ == "bibtex":
        return read_bibtex_file
    if typ == "docx":
        return read_docx_file
    if typ == "txt":
        return read_txt_file
    raise ValueError(f'Unrecognised type of file "{typ}".')

def default_file_writer(typ):
    """
    Return the default file writer for a given type.

    :param typ: The type of file to be written.
    :type typ: str
    :return: The default file writer.
    :rtype: function
    :raises ValueError: if the type is not recognised.
    """
    if typ == "markdown":
        return write_markdown_file
    if typ == "yaml":
        return write_yaml_file
    if typ == "json":
        return write_json_file
    if typ == "bibtex":
        return write_bibtex_file
    if typ == "docx":
        return write_docx_file
    raise ValueError(f'Unrecognised type of file "{typ}".')


def read_file(filename):
    """ "Attempt to read the file given the extention."""
    typ = extract_file_type(filename)
    return default_file_reader(typ)(filename)


def read_yaml_file(filename, compress=None):
    """Read a yaml file and return a python dictionary.

    Trusted-caller I/O: does not confine ``filename``. Configured or
    untrusted names must go through ``extract_full_filename`` first (CIP-000A).
    ``.yml.gz`` is gzip YAML (CIP-0015); a ``.yml`` file whose bytes are
    gzip is an error (no magic-byte decode).
    """
    _raise_if_undeclared_gzip(filename, compress)
    with open_text_store(filename, "r", compress=compress) as stream:
        try:
            log.debug(f'Reading yaml file "{filename}"')
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            log.warning(exc)
            data = {}
    return data


def read_bibtex_file(filename):
    """
    Read a bibtex file and return a python dictionary.

    Trusted-caller I/O: does not confine ``filename`` (CIP-000A).

    :param filename: The filename of the bibtex file.
    :type filename: str
    :return: The data read from the file.
    :rtype: dict
    """
    parser = bp.bparser.BibTexParser()
    parser.ignore_nonstandard_types = False
    parser.homogenize_fields = False
    parser.common_strings = False
    with open(filename, "r") as stream:
        log.debug(f'Reading bibtex file "{filename}"')
        data = bp.load(stream, parser)
    return reorder_dictionary(data.entries, bibtex_column_order)


def yaml_prep(data):
    """
    Prepare any fields for writing in yaml

    :param data: The data to be prepared.
    :type data: dict
    :return: The prepared data.
    :rtype: dict
    """
    writedata = data.copy()
    if type(writedata) is list:
        for num, el in enumerate(writedata):
            writedata[num] = yaml_prep(el)
        return writedata

    for key, item in writedata.items():
        if pd.api.types.is_datetime64_dtype(item) or type(item) is pd.Timestamp:
            writedata[key] = item.strftime("%Y-%m-%d %H:%M:%S.%f")
    return writedata


def write_bibtex_file(data, filename):
    """
    Write a bibtex file from a python dictionary.

    Trusted-caller I/O: does not confine ``filename`` (CIP-000A).

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the bibtex file.
    :type filename: str
    """

    # Ensure that the data ID entries are unique
    ids = []
    for entry in data:
        if "ID" in entry:
            ids.append(entry["ID"])
        else:
            raise ValueError(f"Entry {entry} does not have an ID field.")
    if len(ids) != len(set(ids)):
        raise ValueError(f"There are repeated IDs in the data.")

    # Ensure that the ids are valid keys for bibtex.
    for entry in data:
        # invalid bibtex identifier characters are: @',#}{~% and whitespace characters such as space, tab, newline, and carriage return.
        # Check they aren't in the ID.
        if re.search(r"[@',#}{~% \t\n\r]", entry["ID"]):
            raise ValueError(f"The ID {entry['ID']} contains invalid characters.")

    bibdata = bp.bibdatabase.BibDatabase()
    bibdata.entries = data
    writer = bp.bwriter.BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = bibtex_sort_by
    writer.display_order = bibtex_column_order
    with open(filename, "w") as stream:
        log.debug(f'Writing bibtex file "{filename}".')
        bp.dump(bibdata, stream, writer)


def write_yaml_file(data, filename, compress=None, compress_level=6):
    """
    Write a yaml file from a python dictionary.

    Trusted-caller I/O: does not confine ``filename`` (CIP-000A).
    ``.yml.gz`` writes gzip YAML (CIP-0015).

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the yaml file.
    :type filename: str
    """
    writedata = yaml_prep(data)
    with open_text_store(
        filename, "w", compress=compress, compress_level=compress_level
    ) as stream:
        try:
            log.debug(f'Writing yaml file "{filename}".')
            # Use custom dumper that forces block scalars for multiline strings
            yaml.dump(writedata, stream, Dumper=LynguineSafeDumper, sort_keys=False, allow_unicode=True)
        except yaml.YAMLError as exc:
            log.warning(exc)


def read_yaml_meta_file(filename):
    """
    Read meta information associated with a file as a yaml and return
    a python dictionary if it exists.

    :param filename: The filename of the file.
    :type filename: str
    :return: The meta information.
    :rtype: dict
    """
    metafile = filename + ".yml"
    if os.path.exists(metafile):
        data = read_yaml_file(metafile)
    else:
        data = {}
    return data


def write_yaml_meta_file(data, filename):
    """
    Write meta information associated with a file to a yaml.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the file.
    :type filename: str
    """
    metafile = filename + ".yml"
    write_yaml_file(data, metafile)


def read_markdown_file(filename, include_content=True):
    """
    Read a markdown file and return a python dictionary.

    Trusted-caller I/O: does not confine ``filename`` (CIP-000A).

    :param filename: The filename of the markdown file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    :rtype: dict
    """
    with open(filename, "r") as stream:
        try:
            log.debug(f"Reading markdown file {filename}")
            post = frontmatter.load(stream)
            data = post.metadata
            if include_content:
                data["content"] = post.content
        except yaml.YAMLError as exc:
            log.warning(exc)
            data = {}

    return data


def read_docx_file(filename, include_content=True):
    """
    Read information from a docx file.

    :param filename: The filename of the docx file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    :rtype: dict
    """
    directory = tempfile.gettempdir()
    tmpfile = os.path.join(directory, "tmp.md")
    extra_args = []
    extra_args.append("--standalone")
    extra_args.append("--track-change=all")
    pypandoc.convert_file(
        filename, "markdown", outputfile=tmpfile, extra_args=extra_args
    )
    data = read_markdown_file(tmpfile, include_content)
    return remove_nan(data)


def read_talk_file(filename, include_content=True):
    """
    Read a markdown talk file.

    :param filename: The filename of the talk file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    """
    data = read_markdown_file(filename, include_content)
    return remove_nan(data)


def read_talk_include_file(filename, include_content=True):
    """
    Read a markdown talk include file.

    :param filename: The filename of the talk include file.
    :type filename: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    :return: The data read from the file.
    """
    
    data = read_markdown_file(filename, include_content)
    return remove_nan(data)


def write_url_file(data, filename, content, include_content=True):
    """
    Write a url to a file

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the url file.
    :type filename: str
    :param content: The content of the url file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    # This is with writing links to prefilled google forms in mind.
    raise NotImplementedError("The write url file function has not been implemented.")


def write_markdown_file(data, filename, content=None, include_content=True):
    """
    Write a markdown file from a python dictionary

    Trusted-caller I/O: does not confine ``filename`` (CIP-000A).

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the markdown file.
    :type filename: str
    :param content: The content of the markdown file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    if content is None:
        if include_content and "content" in data:
            write_data = {key: item for (key, item) in data.items() if key != "content"}
            content = data["content"]
        else:
            if not include_content:
                content = ""
            write_data = data
    else:
        write_data = data.copy()
        if "content" in data:
            del write_data["content"]
    log.debug(f'Writing markdown file "{filename}"')
    if pd.isna(content):
        content = ""
    post = frontmatter.Post(content, **write_data)
    # Serialize ourselves: older python-frontmatter ``dump`` encodes to bytes
    # and expects a binary file; newer versions write ``str`` and expect text
    # mode. ``dumps`` returns str in both — encode once and write binary.
    text = frontmatter.dumps(post, sort_keys=False)
    raw = text if isinstance(text, bytes) else text.encode("utf-8")
    with open(filename, "wb") as stream:
        stream.write(raw)

def create_document_content(**kwargs):
    """
    Create a document content from the arguments.
    :param content: The content of the document.
    :type content: str
    :param filename: The filename of the document.
    :type filename: str
    :param directory: The directory of the document.
    :type directory: str
    :return: The data, filename and content of the document.
    :rtype: tuple
    """
    filename = extract_full_filename(kwargs)
    if "content" in kwargs:
        content = kwargs["content"]
    else:
        content = ""
    data = {}
    for key, item in kwargs.items():
        if key not in ["filename", "directory", "content"]:
            data[key] = item
    return data, filename, content
        

def create_letter(**kwargs):
    """
    Create a markdown letter.
    :param content: The content of the letter.
    :type content: str
    :param filename: The filename of the letter.
    :type filename: str
    :param directory: The directory of the letter.
    :type directory: str
    :return: The data, filename and content of the letter.
    :rtype: tuple
    """
    data, filename, content = create_document_content(**kwargs)
    write_letter_file(data=data, filename=filename, content=content)

    
def write_letter_file(data, filename, content, include_content=True):
    """
    Write a letter file from a python dictionary

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the letter.
    :type filename: str
    :param content: The content of the letter.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    if include_content and content in data:
        write_data = {key: item for (key, item) in data.items() if key != "content"}
        content = data[content]
    else:
        if not include_content:
            content = ""
        write_data = data

    log.debug(f'Writing markdown letter file "{filename}"')
    post = frontmatter.Post(content, **write_data)
    # Same version-safe write as write_markdown_file (dumps → utf-8 → wb).
    text = frontmatter.dumps(post, sort_keys=False)
    raw = text if isinstance(text, bytes) else text.encode("utf-8")
    with open(filename, "wb") as stream:
        stream.write(raw)


def write_formlink(data, filename, content, include_content=True):
    """
    Write a url to prepopulate a Google form
    """
    write_url_file(data, filename, content, include_content)


def write_docx_file(data, filename, content, include_content=True):
    """
    Write a docx file from a python dictionary.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the docx file.
    :type filename: str
    :param content: The content of the docx file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    directory = tempfile.gettempdir()
    tmpfile = os.path.join(directory, "tmp.md")
    write_markdown_file(data, tmpfile, content, include_content)
    log.debug(f'Converting markdown file "{tmpfile}" to docx file "{filename}"')
    extra_args = []
    if "reference-doc" in data:
        extra_args.append("--reference-doc=" + data["reference-doc"])
    pypandoc.convert_file(tmpfile, "docx", outputfile=filename, extra_args=extra_args)


def write_tex_file(data, filename, content, include_content=True):
    """
    Write a docx file from a python dictionary.

    :param data: The data to be written.
    :type data: dict
    :param filename: The filename of the docx file.
    :type filename: str
    :param content: The content of the docx file.
    :type content: str
    :param include_content: Whether to include the content in the data.
    :type include_content: bool
    """
    directory = tempfile.gettempdir()
    tmpfile = os.path.join(directory, "tmp.md")
    write_markdown_file(data, tmpfile, content, include_content)
    log.debug(f'Converting markdown file "{tmpfile}" to tex file "{filename}"')
    extra_args = []
    pypandoc.convert_file(tmpfile, "tex", outputfile=filename, extra_args=extra_args)


def read_csv(details):
    """
    Read data from a csv file.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    dtypes = extract_dtypes(details)
    filename = extract_full_filename(details)
    if "header" in details:
        header = details["header"]
    else:
        header = 0

    if "delimiter" in details:
        delimiter = details["delimiter"]
    else:
        delimiter = ","

    if "quotechar" in details:
        quotechar = details["quotechar"]
    else:
        quotechar = '"'
    log.debug(
        f'Reading csv file "{filename}" from row "{header}" with quote character {quotechar} and delimiter "{delimiter}"'
    )

    data = pd.read_csv(
        filename,
        dtype=dtypes,
        header=header,
        delimiter=delimiter,
        quotechar=quotechar,
    )
    return data


def read_parquet(details):
    """Read a parquet table (CIP-0015 phase 2). Requires ``lynguine[parquet]``."""
    _pa, pq = _import_pyarrow()
    filename = extract_full_filename(details)
    log.debug(f'Reading parquet file "{filename}"')
    table = pq.read_table(filename)
    return _python_lists_from_parquet(table.to_pandas())


def read_excel(details):
    """
    Read data from an excel spreadsheet.

    :param details: The details of the file to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    
    dtypes = extract_dtypes(details)
    filename = extract_full_filename(details)
    if "header" in details:
        header = details["header"]
    else:
        header = 0

    if "sheet" in details:
        sheet_name = details["sheet"]
    else:
        sheet_name = "Sheet1"
    log.debug(
        f'Reading excel file "{filename}" sheet "{sheet_name}" from row "{header}"'
    )

    data = pd.read_excel(
        filename,
        sheet_name=sheet_name,
        dtype=dtypes,
        header=header,
    )

    return data


def _uniquify_index_values(values):
    """Disambiguate later duplicate index labels by appending `` (n)``.

    Fake generators such as ``name`` are not unique. ``from_flow`` drops
    duplicate non-series indexes, so a declared fake index must be unique
    or ``nrows`` is silently reduced.
    """
    seen = {}
    unique = []
    for value in values:
        count = seen.get(value, 0) + 1
        seen[value] = count
        if count == 1:
            unique.append(value)
        else:
            unique.append(f"{value} ({count})")
    return unique


def read_fake(details):
    """
    Read data from an artificially generated source.

    When ``index`` names a generated column, later duplicate values in that
    column are disambiguated so the frame keeps ``nrows`` after
    ``from_flow`` sets the index.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read from the source.
    :rtype: pandas.DataFrame
    """

    if not isinstance(details, dict):
        errmsg = "\"fake\" specified in config but not in form of a dictionary."
        log.error(errmsg)
        raise ValueError(errmsg)

    required_keys = ["nrows", "cols"]
    for key in required_keys:
        if key not in details:
            errmsg = f"\"fake\" specified in config but missing \"{key}\" key."
            log.error(errmsg)
            raise ValueError(errmsg)
        
    if isinstance(details["cols"], list):
        log.info("\"cols\" for fake data specified as a list, converting to dictionary with all columns set to the given name of column.")
        cols_are_attributes = [hasattr(Generate, col) for col in details["cols"]]
        if all(cols_are_attributes):
            details["cols"] = {col: col for col in details["cols"]}
        else:
            # Extract which columns aren't attributes and return in error message.
            wrong_cols = [col for col, is_attr in zip(details["cols"], cols_are_attributes) if not is_attr]
            errmsg = f"\"fake\" specified as the type and columns are provided as a list, but the following columns are not attributes of lynguine.util.fake.Generate: \"{', '.join(wrong_cols)}\""
            log.error(errmsg)
            raise ValueError(errmsg)
        
    if not isinstance(details["cols"], dict):
        errmsg = ("\"fake\" specified in config which requires that cols are specified as a dictionary, "
                  "with dictionary entries representing the type of fake data to be generated.")
        log.error(errmsg)
        raise ValueError(errmsg)

    if not isinstance(details["nrows"], int) or details["nrows"] < 0:
        errmsg = "\"nrows\" must be a non-negative integer."
        log.error(errmsg)
        raise ValueError(errmsg)

    cols = details['cols']  # Correct reference to cols
    for col, gen in cols.items():
        if hasattr(Generate, gen):
            gen_func = getattr(Generate, gen)
            if callable(gen_func):
                cols[col] = gen_func
            else:
                errmsg = f"\"fake\" specified in config but \"{gen}\" is not a callable function attribute of lynguine.util.fake.Generate."
                if list_convert:
                    errmsg += " This is likely because the \"cols\" were specified as a list and not a dictionary, meaning that in dictionary conversion I've created columns where the function attributes match the column title."
                log.error(errmsg)
                raise ValueError(errmsg)
        else:
            errmsg = f"\"{gen}\" specified as column's fake function, \"{gen}\" is not an attribute of lynguine.util.fake.Generate."
            log.error(errmsg)
            raise ValueError(errmsg)

    data = []
    for _ in range(details["nrows"]):
        row = {col: gen() for col, gen in cols.items()}
        data.append(row)

    df = pd.DataFrame(data)
    index_column = details.get("index")
    if isinstance(index_column, str) and index_column in df.columns:
        if df[index_column].duplicated().any():
            duplicates = df.loc[df[index_column].duplicated(keep="first"), index_column]
            duplicate_names = [str(value) for value in duplicates.tolist()]
            log.warning(
                f"Duplicate fake index values in column \"{index_column}\": "
                f"\"{', '.join(duplicate_names)}\". Disambiguating later copies."
            )
            df[index_column] = _uniquify_index_values(df[index_column])
    return df
    
    
def read_local(details):
    """
    Read data directly from details file.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read from the settings file..
    :rtype: pandas.DataFrame
    :raises ValueError: If the 'details' is not a dictionary or is missing required keys.
    """

    if not isinstance(details, dict):
        errmsg = "\"local\" specified in config but not in form of a dictionary."
        log.error(errmsg)
        raise ValueError(errmsg)

    # Create data frame from details
    
    try:
        data = details["data"]
        # Handle scalar dictionaries (e.g., for parameters/constants)
        if isinstance(data, dict) and all(not isinstance(v, (list, dict)) for v in data.values()):
            # All values are scalars - provide an index
            index_name = details.get("index", "value")
            df = pd.DataFrame(data, index=[index_name])
        else:
            df = pd.DataFrame(data=data)
    except KeyError as e:
        errmsg = f"Could not create data frame from details specified in \"local\" entry. Missing key {e}."
        log.error(errmsg)
        raise ValueError(errmsg)
    except Exception as e:
        errmsg = f"Could not create data frame from details specified in \"local\" entry. {e}"
        log.error(errmsg)
        raise ValueError(errmsg)

    # Optionally set index name if not already set
    if df.index.name is None:
        log.debug('Index name not set in data frame. Setting to "index".')
        df.index.name = "index"

    return df

if GSPREAD_AVAILABLE:

    def read_gsheet(details):
        """
        Read data from a Google sheet using secure credential management.

        :param details: The details of the file to be read.
        :type details: dict
        :return: The data read from the file.
        :rtype: pandas.DataFrame
        :raises ValueError: If credentials cannot be retrieved
        """
        dtypes = extract_dtypes(details)
        filename = extract_full_filename(details)
        log.debug(f"Reading Google sheet named {filename}")
        sheet = extract_sheet(details)
        
        # Use secure credential management
        gconfig = _get_google_sheets_config(details)
        
        gsheet = gspd.Spread(
            spread=filename,
            sheet=sheet,
            config=gconfig,
        )
        data = gsheet.sheet_to_df(
            index=None,
            header_rows=details["header"] + 1,
            start_row=details["header"] + 1,
        )
        return data


def write_excel(df, details):
    """
    Write data to an excel spreadsheet.

    :param df: The data to be written.
    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    if "header" in details:
        header = details["header"]
    else:
        header = 0

    if "sheet" in details:
        sheet_name = details["sheet"]
    else:
        sheet_name = "Sheet1"

    log.debug(
        f'Writing excel file "{filename}" sheet "{sheet_name}" header at row "{header}".'
    )

    writer = pd.ExcelWriter(
        filename, engine="xlsxwriter", datetime_format="YYYY-MM-DD HH:MM:SS.000"
    )
    sheet_name = details["sheet"]
    df.to_excel(writer, sheet_name=sheet_name, startrow=header, index=False)
    writer.close()


def write_csv(df, details):
    """
    Write data to an csv spreadsheet.

    The path is confined via ``extract_full_filename`` (CIP-000A). The
    following ``open()`` is still a trusted-caller primitive as far as
    CodeQL is concerned (CIP-000D cluster A).

    :param df: The data to be written.
    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param details: The details of the file to be written.
    :type details: dict
    """
    filename = extract_full_filename(details)
    if "delimiter" in details:
        delimiter = details["delimiter"]
    else:
        delimiter = ","

    if "quotechar" in details:
        quotechar = details["quotechar"]
    else:
        quotechar = '"'
    log.debug(
        f'Writing csv file "{filename}" with quote character {quotechar} and delimiter "{delimiter}"'
    )

    with open(filename, "w") as stream:
        df.to_csv(
            stream,
            sep=delimiter,
            quotechar=quotechar,
            header=True,
            index=False,
        )


def write_parquet(df, details):
    """Write a parquet table with list<float32> numeric list columns.

    Requires ``lynguine[parquet]``. Default codec is snappy; set
    ``compress: zstd`` (or gzip/brotli/lz4/none) to override.
    """
    pa, pq = _import_pyarrow()
    filename = extract_full_filename(details)
    compression = _parquet_compression(details)
    log.debug(f'Writing parquet file "{filename}" with compression "{compression}"')
    table = _dataframe_to_arrow_table(df, details, pa)
    pq.write_table(table, filename, compression=compression)


if GSPREAD_AVAILABLE:

    def write_gsheet(df, details):
        """
        Write data to a Google sheet using secure credential management.

        :param df: The data to be written.
        :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
        :param details: The details of the file to be written.
        :type details: dict
        :raises ValueError: If credentials cannot be retrieved
        """
        filename = extract_full_filename(details)
        sheet = extract_sheet(details)
        log.debug(f"Writing Google sheet named {filename}")
        
        # Use secure credential management
        gconfig = _get_google_sheets_config(details)
        
        gsheet = gspd.Spread(
            spread=filename,
            sheet=sheet,
            create_spread=True,
            config=gconfig,
        )
        gsheet.df_to_sheet(
            df=df,
            index=False,
            headers=True,
            replace=True,
            sheet=sheet,
            start=(details["header"] + 1, 1),
        )


directory_readers = [
    {
        "default_glob": "*.yml",
        "filereader": read_yaml_file,
        "name": "read_yaml_directory",
        "docstr": "Read a directory of yaml files.",
    },
    {
        "default_glob": "*.json",
        "filereader": read_json_file,
        "name": "read_json_directory",
        "docstr": "Read a directory of json files.",
    },
    {
        "default_glob": "*.bib",
        "filereader": read_bibtex_file,
        "name": "read_bibtex_directory",
        "docstr": "Read a directory of bibtex files.",
    },
    {
        "default_glob": "*.md",
        "filereader": read_markdown_file,
        "name": "read_markdown_directory",
        "docstr": "Read a directory of markdown files.",
    },
    {
        "default_glob": "*",
        "filereader": read_file,
        "name": "read_plain_directory",
        "docstr": "Read a directory of files.",
    },
    {
        "default_glob": "*",
        "filereader": read_yaml_meta_file,
        "name": "read_meta_directory",
        "docstr": "Read a directory of yaml meta files.",
    },
    {
        "default_glob": "*.docx",
        "filereader": read_docx_file,
        "name": "read_docx_directory",
        "docstr": "Read a directory of word files.",
    },
]


directory_writers = [
    {
        "filewriter": write_json_file,
        "name": "write_json_directory",
        "docstr": "Write a directory of json files.",
    },
    {
        "filewriter": write_yaml_file,
        "name": "write_yaml_directory",
        "docstr": "Write a directory of yaml files.",
    },
    {
        "filewriter": write_markdown_file,
        "name": "write_markdown_directory",
        "docstr": "Write a directory of markdown files.",
    },
    {
        "filewriter": write_yaml_meta_file,
        "name": "write_meta_directory",
        "docstr": "Write a directory of yaml meta files.",
    },
]


def gdrf_(default_glob, filereader, name="", docstr=""):
    """
    Function generator for different directory readers.

    :param default_glob: The default glob to be used for the directory reader.
    :type default_glob: str
    :param filereader: The function to be used to read the files.
    :type filereader: function
    :param name: The name of the function to be created.
    :type name: str
    :param docstr: The docstring for the function to be created.
    :type docstr: str
    :return: The function to be created.
    :rtype: function
    """

    def directory_reader(details):
        """
        Return a function for reading the directory.

        :param details: The details of the directory to be read.
        :type details: dict
        :return: The directory reader function
        :rtype: function
        """
        
        details = update_store_fields(details)
        globname = None
        if "glob" in details:
            globname = details["glob"]
        if globname is None or globname == "":
            globname = default_glob
        if "source" in details:
            source = details["source"]
        else:
            source = None
        return read_directory(
            details=details,
            filereader=filereader,
            default_glob=globname,
            source=source,
        )

    directory_reader.__name__ = name
    directory_reader.__doc__ = docstr
    return directory_reader


def update_store_fields(details):
    """
    Add default store fields values

    :param details: The details to update with.
    :type details: dict
    :return: The updated details.
    :rtype: dict
    """
    # TK: Perhaps this should be set in config defaults somewhere.
    # Extracts info about where the directory read file data is to be written.
    if "store_fields" not in details:
        details["store_fields"] = {
            "directory": "sourceDirectory",
            "filename": "sourceFilename",
            "root": "sourceRoot",
        }
    else:
        if "directory" not in details["store_fields"]:
            details["store_fields"]["directory"] = "sourceDirectory"
        if "filename" not in details["store_fields"]:
            details["store_fields"]["filename"] = "sourceFilename"
        if "root" not in details["store_fields"]:
            details["store_fields"]["root"] = "sourceRoot"
    return details


def gdwf_(filewriter, name="", docstr=""):
    """
    Function generator for different directory writers.

    :param filewriter: The function to be used to write the files.
    :type filewriter: function
    :param name: The name of the function to be created.
    :type name: str
    :param docstr: The docstring for the function to be created.
    :type docstr: str
    :return: The function to be created.
    :rtype: function
    """

    def directory_writer(df, details):
        """
        Return a function for writing the directory.

        :param df: The data to be written.
        :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
        :param details: The details of the directory to be written.
        :type details: dict
        :return: The directory writer function
        :rtype: function
        """
        details = update_store_fields(details)
        return write_directory(
            df=df,
            details=details,
            filewriter=filewriter,
        )

    directory_writer.__name__ = name
    directory_writer.__doc__ = docstr
    return directory_writer


def populate_directory_readers(readers):
    """
    Populate the directory readers automatically creates functions for reading directories.

    :param readers: The readers to be created.
    :type readers: list
    """
    this_module = sys.modules[__name__]
    for reader in readers:
        setattr(
            this_module,
            reader["name"],
            gdrf_(**reader),
        )


def populate_directory_writers(writers):
    """
    This function automatically create functions for writing directories.

    :param writers: The writers to be created.
    :type writers: list
    """
    this_module = sys.modules[__name__]
    for writer in writers:
        setattr(
            this_module,
            writer["name"],
            gdwf_(**writer),
        )


populate_directory_readers(directory_readers)
populate_directory_writers(directory_writers)


def finalize_data(df : pd.DataFrame, interface : Interface) -> tuple[pd.DataFrame, Interface]:
    """
    Finalize the data frame by augmenting with any columns.

    :param df: The data frame to be finalized.
    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param interface: The interface of the data frame.
    :type interface: lynguine.config.interface.Interface
    :return: The finalized data frame.
    :rtype: pandas.DataFrame or lynguine.data.CustomDataFrame
    """

    # Eventually this should do any augmentation that isn't required
    # by the series. The problem is at the moment the liquid rendering
    # (and other renderings) are too integrated with assess. They need
    # to be pulled out and not so dependent on the data structure.

    if df.index.name is None:
        if "index" in interface:
            index = interface["index"]
            if type(index) is dict:
                df.index.name = index["name"]
            elif type(index) is str:
                df.index.name = index
            else:
                self._log.warning(
                    f'Index "{index}" present in interface but no valid name found.'
                )
    # Add these columns if they are not present.          
    if "add_columns" in interface:
        for col in interface["add_columns"]:
            if col not in df.columns:
                df[col] = None

    # rename these columns            
    if "rename_columns" in interface:
        for col in interface["rename_columns"]:
            cols = df.columns
            if col not in cols:
                raise ValueError(
                    f'rename_columns contains key "{col}" which is not a column in the loaded DataFrame. Columns are "{cols}"'
                )
        df.rename(columns=interface["rename_columns"], inplace=True)

    # drop these columns
    if "ignore_columns" in interface:
        for col in interface["ignore_columns"]:
            cols = df.columns
            if col not in cols:
                raise ValueError(
                    f'ignore_columns contains key "{col}" which is not a column in the loaded DataFrame. Columns are "{cols}"'
                )
        df.drop(columns=interface["ignore_columns"], inplace=True)

    if "select_columns" in interface:
        df = df.loc[:, interface["select_columns"]]
        del interface["select_columns"]

    # Add missing columns declared in "columns" before compute runs,
    # so that row_args referencing sparse or all-NaN columns don't KeyError.
    # (_finalize_df in data.py does the same, but runs after compute.)
    if "columns" in interface:
        missing = [col for col in interface["columns"] if col not in df.columns]
        if missing:
            missing_df = pd.DataFrame({col: None for col in missing}, index=df.index)
            df = pd.concat([df, missing_df], axis=1)

    if "compute" in interface:
            compute = Compute.from_flow(interface)
            for comp in compute.computes:
                compute_prep = compute.prep(comp, df)
                fargs = compute_prep["args"]
                if "field" in comp: # if field is in compute, then we are computing or updating a new field
                    for ind in df.index:
                        df.loc[ind, comp["field"]] = compute_prep["function"](df.loc[ind], **fargs)

                else:
                    errmsg = f"Compute object in interface file is missing field key."
                    log.error(errmsg)
                    raise ValueError(errmsg)
   

    return df, interface


def read_hstack(details):
    """
    Read data from a horizontal stack of data sources.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    
    if details.get('type') != 'hstack':
        raise ValueError('Expected details type to be "hstack".')

    if 'specifications' not in details:
        raise ValueError('Details must include "specifications".')

    # Initialize an empty list to hold DataFrames
    dfs = []

    # Iterate over each data source in the details
    for specs in details['specifications']:
        # Read each DataFrame using the read_data function
        df, _ = read_data(specs)        
        dfs.append(df)

        # Set default values if not provided in specs
        specs.setdefault('on', 'index')
        specs.setdefault('how', 'left')
        specs.setdefault('lsuffix', '')
        specs.setdefault('rsuffix', '_right')

    if not dfs:
        raise ValueError('No data sources provided for hstack.')

    # Initialize final_df for horizontal stacking
    final_df = None

    # Iterate over the list of DataFrames and their corresponding details
    for df, specs in zip(dfs, details['specifications']):
        if final_df is None:
            final_df = df
        else:
            if specs['on'] == 'index':
                # Make the column specifided in the specs "index" field the index of the frame.
                if "index" in specs:
                    df.set_index(specs['index'], inplace=True)
                if "index" in details:
                    final_df.set_index(details['index'], inplace=True)
                df = _drop_join_suffix_collisions(
                    final_df, df, specs['lsuffix'], specs['rsuffix']
                )
                final_df = final_df.join(df, how=specs['how'], lsuffix=specs['lsuffix'], rsuffix=specs['rsuffix'])
                # Remove the index column again
                if "index" in details:
                    final_df[details['index']] = final_df.index
                    final_df.reset_index(drop=True, inplace=True)
                
            else:
                right = _drop_merge_suffix_collisions(
                    final_df, df, specs['on'], specs['lsuffix'], specs['rsuffix']
                )
                final_df = pd.merge(
                    final_df,
                    right,
                    on=specs['on'],
                    how=specs['how'],
                    suffixes=(specs['lsuffix'], specs['rsuffix']),
                )

    return final_df


def _drop_join_suffix_collisions(left, right, lsuffix, rsuffix):
    """Drop right columns whose suffixed names already exist on left.

    A prior join may have created ``col{rsuffix}``. Joining another frame that
    also has ``col`` would try to create the same name again and raise
    ``MergeError``. Earlier columns win; the colliding right column is dropped.
    """
    if right is None or right.empty:
        return right
    drop = []
    for col in right.columns.intersection(left.columns):
        right_name = f"{col}{rsuffix}" if rsuffix else col
        if right_name in left.columns:
            drop.append(col)
            continue
        if lsuffix:
            left_name = f"{col}{lsuffix}"
            if left_name in left.columns and left_name != col:
                drop.append(col)
    if drop:
        return right.drop(columns=drop)
    return right


def _drop_merge_suffix_collisions(left, right, on, lsuffix, rsuffix):
    """Same collision policy as ``_drop_join_suffix_collisions`` for merges."""
    if right is None or right.empty:
        return right
    on_cols = [on] if isinstance(on, str) else list(on)
    drop = []
    overlap = left.columns.intersection(right.columns)
    for col in overlap:
        if col in on_cols:
            continue
        right_name = f"{col}{rsuffix}" if rsuffix else col
        if right_name in left.columns:
            drop.append(col)
            continue
        if lsuffix:
            left_name = f"{col}{lsuffix}"
            if left_name in left.columns and left_name != col:
                drop.append(col)
    if drop:
        return right.drop(columns=drop)
    return right

def read_stack(details):
    """
    Read data from a horizontal stack of data series, where each source is a single-row DataFrame.
    Returns a single-row DataFrame combining all sources.

    :param details: The details of the data series to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    
    if details.get('type') != 'stack':
        raise ValueError('Expected details type to be "stack".')

    if 'specifications' not in details:
        raise ValueError('Details must include "specifications".')

    # Initialize final DataFrame with one row
    final_df = pd.DataFrame(index=[0])

    # Iterate over each data source in the details
    for specs in details['specifications']:
        # Read each DataFrame using the read_data function
        df, _ = read_data(specs)
        
        # Verify we have a DataFrame with exactly one row
        if not isinstance(df, pd.DataFrame):
            raise ValueError('Each specification must result in a DataFrame')
        if len(df.index) != 1:
            raise ValueError(f'Each specification must result in a single row DataFrame. Got {len(df.index)} rows')
            
        # Add columns from this DataFrame to final_df
        for col in df.columns:
            final_df[col] = df[col].iloc[0]

    if len(final_df.columns) == 0:
        raise ValueError('No data sources provided for stack.')

    return final_df
    

def read_vstack(details):
    """
    Read data from a vertical stack of data sources.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read from the file.
    :rtype: pandas.DataFrame
    """
    
    if details.get('type') != 'vstack':
        raise ValueError('Expected details type to be "vstack".')

    # 'specifications' provides the file details for the data sources to be stacked (list of dicts)
    if 'specifications' not in details:
        raise ValueError('Details must include "specifications".')

    dfs = []
    for specs in details['specifications']:
        df, _ = read_data(specs)
        dfs.append(df)

    if not dfs:
        raise ValueError('No data sources provided for vstack.')

    # Option for resetting index
    reset_index = details.get('reset_index', False)

    # Perform vertical stacking
    stacked_df = pd.concat(dfs, axis=0, ignore_index=reset_index)
    
    return stacked_df

def read_series(details):
    """
    Read in the series data from the details given in configuration. A series type is a data frame where the indices aren't unique. If read in as a series, then each entry in each column of data frame is converted to a list, where the number of elements of the list are the number of non-unique elements from the index.

    :param details: The details of the series data to be read.
    :type details: dict
    :return: The data read in.
    :rtype: pandas.DataFrame
    """
    if "index" not in details:
        raise ValueError('Field "index" missing in data source details for read_series.')
    
    df, _ = read_data(details=details["specifications"])

    df.set_index(details["index"], inplace=True)
    unique_index = df.index.unique()
    newdf = pd.DataFrame(index=unique_index, columns=[details["index"]] + list(df.columns), dtype="object")
    for ind in unique_index:
        # Compute how many times the index should be repeated.
        ind_length = len(df.loc[ind].index)
        newdf.at[ind, details["index"]] = ind
        for col in df.columns:
            if isinstance(df.loc[ind, col], pd.Series):
                newdf.at[ind, col] = df.loc[ind, col].to_list()
            else:
                newdf.at[ind, col] = [df.loc[ind, col]]
            
    newdf.reset_index(drop=True, inplace=True)
    return newdf


def _validate_wide_flatten_order(order: str) -> None:
    if order not in ("index_then_field", "field_then_index"):
        errmsg = (
            f'wide_flatten order must be "index_then_field" or '
            f'"field_then_index", got "{order}".'
        )
        log.error(errmsg)
        raise ValueError(errmsg)


def _validate_wide_flatten_index(index, separator: str) -> None:
    if not index.is_unique:
        duplicates = index[index.duplicated()].unique().tolist()
        errmsg = (
            "wide_flatten requires a unique index (cannot unstack "
            f"ambiguously). Duplicate labels: {duplicates}."
        )
        log.error(errmsg)
        raise ValueError(errmsg)
    for label in index:
        label_str = str(label)
        if separator and separator in label_str:
            errmsg = (
                f'wide_flatten separator "{separator}" appears in index '
                f'label "{label_str}". Choose a separator that does not '
                "occur in index strings (v1 policy)."
            )
            log.error(errmsg)
            raise ValueError(errmsg)


def compose_wide_column_name(key, field, *, separator: str = "_", order: str = "index_then_field") -> str:
    """Build a wide column name from index key and field (CIP-0010)."""
    _validate_wide_flatten_order(order)
    key_s, field_s = str(key), str(field)
    if order == "index_then_field":
        return f"{key_s}{separator}{field_s}"
    return f"{field_s}{separator}{key_s}"


def parse_wide_column_name(
    name,
    *,
    separator: str = "_",
    order: str = "index_then_field",
    keys,
    fields=None,
):
    """Parse a wide column name into ``(key, field)`` (CIP-0010 Pattern A).

    ``keys`` are the authoritative index labels (e.g. from ``flattenKeys``).
    Matching prefers longer key strings so one key is not a prefix of another.
    When ``fields`` is given, names must match an exact key/field composition;
    otherwise the remainder after the key+separator is the field name.

    :return: ``(key, field)`` where ``key`` is the object from ``keys``.
    """
    _validate_wide_flatten_order(order)
    name_s = str(name)
    keyed = sorted(list(keys), key=lambda k: len(str(k)), reverse=True)
    if not keyed:
        errmsg = f'Cannot parse wide name "{name_s}": no keys provided.'
        log.error(errmsg)
        raise ValueError(errmsg)

    if fields is not None:
        field_list = list(fields)
        for key in keyed:
            for field in field_list:
                expected = compose_wide_column_name(
                    key, field, separator=separator, order=order
                )
                if name_s == expected:
                    return key, field
        errmsg = (
            f'Cannot parse wide name "{name_s}" with separator={separator!r} '
            f"order={order!r}, keys={list(map(str, keyed))}, "
            f"fields={list(map(str, field_list))}."
        )
        log.error(errmsg)
        raise ValueError(errmsg)

    if order == "index_then_field":
        for key in keyed:
            prefix = f"{key}{separator}"
            if name_s.startswith(prefix) and len(name_s) > len(prefix):
                return key, name_s[len(prefix) :]
    else:
        for key in keyed:
            suffix = f"{separator}{key}"
            if name_s.endswith(suffix) and len(name_s) > len(suffix):
                return name_s[: -len(suffix)], key

    errmsg = (
        f'Cannot parse wide name "{name_s}" with separator={separator!r} '
        f"order={order!r} and keys={list(map(str, keyed))}."
    )
    log.error(errmsg)
    raise ValueError(errmsg)


def wide_flatten_dataframe(
    df: pd.DataFrame,
    *,
    separator: str = "_",
    order: str = "index_then_field",
    columns: list | None = None,
    keys_field: str | None = "flattenKeys",
) -> pd.DataFrame:
    """Reshape many rows into one row with index-augmented column names (CIP-0010).

    Turns an ``N × M`` DataFrame with a **unique** index into a ``1 × (N×M)``
    frame whose column names are ``{index}{separator}{field}`` (or
    ``{field}{separator}{index}`` when ``order`` is ``field_then_index``).

    When ``keys_field`` is set (default ``flattenKeys``), the wide row also
    carries an ordered list of former index labels for Liquid/view loops.
    Pass ``keys_field=None`` to omit that column.

    Empty input (no rows) yields a single empty row (plus empty ``keys_field``
    list when enabled). Optional ``columns`` selects value fields to widen;
    other columns are dropped (not kept as globals).

    v1 policy: ``separator`` must not appear in ``str(index)`` labels so
    names stay unambiguously splittable.

    :param df: Source frame; the current index labels identify each former row.
    :param separator: Joiner between index and field in output names.
    :param order: ``index_then_field`` or ``field_then_index``.
    :param columns: Optional subset of value columns to widen.
    :param keys_field: Column name for the ordered key list, or ``None`` to omit.
    :return: Single-row DataFrame with flat string column names.
    :raises ValueError: On invalid ``order``, non-unique index, unknown
        ``columns``, keys field collision, or separator in an index label.
    """
    _validate_wide_flatten_order(order)

    if not isinstance(df, pd.DataFrame):
        errmsg = f"wide_flatten expects a pandas DataFrame, got {type(df).__name__}."
        log.error(errmsg)
        raise ValueError(errmsg)

    work = df
    if columns is not None:
        missing = [c for c in columns if c not in work.columns]
        if missing:
            errmsg = (
                f"wide_flatten columns not present in DataFrame: {missing}. "
                f"Available columns: {list(work.columns)}."
            )
            log.error(errmsg)
            raise ValueError(errmsg)
        work = work.loc[:, list(columns)]

    _validate_wide_flatten_index(work.index, separator)

    if keys_field is not None and keys_field in work.columns:
        errmsg = (
            f'wide_flatten keys_field "{keys_field}" collides with a value '
            "column. Rename keys_field or omit that column from columns."
        )
        log.error(errmsg)
        raise ValueError(errmsg)

    keys_list = list(work.index)

    if work.shape[0] == 0:
        # One empty row; optional empty key list for Liquid loops.
        if keys_field is None:
            return pd.DataFrame(index=[0])
        return pd.DataFrame({keys_field: [[]]}, index=[0])

    # stack → MultiIndex (index, field); unstack → (field, index)
    if order == "index_then_field":
        try:
            series = work.stack(future_stack=True)
        except TypeError:
            # pandas < 2.1
            series = work.stack()
    else:
        series = work.unstack()

    wide = series.to_frame().T
    wide.columns = [
        separator.join(map(str, col if isinstance(col, tuple) else (col,)))
        for col in wide.columns
    ]
    wide.index = pd.RangeIndex(len(wide))
    if keys_field is not None:
        if keys_field in wide.columns:
            errmsg = (
                f'wide_flatten keys_field "{keys_field}" collides with a '
                "widened column name."
            )
            log.error(errmsg)
            raise ValueError(errmsg)
        wide[keys_field] = [keys_list]
    return wide


def wide_unflatten_dataframe(
    wide: pd.DataFrame,
    *,
    separator: str = "_",
    order: str = "index_then_field",
    keys_field: str | None = "flattenKeys",
    fields: list | None = None,
) -> pd.DataFrame:
    """Inverse of materialized :func:`wide_flatten_dataframe` (CIP-0010 Pattern B).

    Rebuilds a tall frame from a single wide row. Uses ``keys_field`` (default
    ``flattenKeys``) for index labels when present; otherwise keys must be
    recoverable from column names via ``fields`` or parse rules.

    Not the default Save path for catalogs — prefer Pattern A virtual views.
    """
    _validate_wide_flatten_order(order)

    if not isinstance(wide, pd.DataFrame):
        errmsg = (
            f"wide_unflatten expects a pandas DataFrame, got {type(wide).__name__}."
        )
        log.error(errmsg)
        raise ValueError(errmsg)

    if len(wide) == 0:
        return pd.DataFrame()
    if len(wide) != 1:
        errmsg = (
            f"wide_unflatten expects a single wide row, got {len(wide)} rows."
        )
        log.error(errmsg)
        raise ValueError(errmsg)

    row = wide.iloc[0]
    value_columns = [c for c in wide.columns if c != keys_field]

    if keys_field is not None and keys_field in wide.columns:
        keys = list(row[keys_field])
    else:
        keys = None

    if not value_columns:
        if keys is not None:
            return pd.DataFrame(index=pd.Index(keys))
        return pd.DataFrame()

    if keys is None:
        if fields is None:
            errmsg = (
                "wide_unflatten needs keys_field on the wide row or an explicit "
                "fields list to recover keys from column names."
            )
            log.error(errmsg)
            raise ValueError(errmsg)
        # Recover keys by parsing all names with a growing key set from fields.
        # Require fields so each name splits uniquely: try all columns and
        # collect keys from successful parses using fields-only matching after
        # a first pass that discovers keys from field-then-index / known fields.
        discovered = []
        for col in value_columns:
            # Without keys, only field_then_index with fields is ambiguous;
            # require keys_field for robustness unless fields given — then
            # split by matching field suffix/prefix.
            matched = False
            for field in fields:
                if order == "index_then_field":
                    suffix = f"{separator}{field}"
                    if str(col).endswith(suffix) and len(str(col)) > len(suffix):
                        key = str(col)[: -len(suffix)]
                        if key not in discovered:
                            discovered.append(key)
                        matched = True
                        break
                else:
                    prefix = f"{field}{separator}"
                    if str(col).startswith(prefix) and len(str(col)) > len(prefix):
                        key = str(col)[len(prefix) :]
                        if key not in discovered:
                            discovered.append(key)
                        matched = True
                        break
            if not matched:
                errmsg = (
                    f'wide_unflatten cannot recover key from column "{col}" '
                    f"with fields={fields}."
                )
                log.error(errmsg)
                raise ValueError(errmsg)
        keys = discovered

    _validate_wide_flatten_index(pd.Index(keys), separator)

    field_names = list(fields) if fields is not None else None
    if field_names is None:
        field_names = []
        for col in value_columns:
            _, field = parse_wide_column_name(
                col, separator=separator, order=order, keys=keys, fields=None
            )
            if field not in field_names:
                field_names.append(field)

    tall = pd.DataFrame(index=pd.Index(keys), columns=field_names, dtype="object")
    for col in value_columns:
        key, field = parse_wide_column_name(
            col, separator=separator, order=order, keys=keys, fields=field_names
        )
        tall.at[key, field] = row[col]
    return tall


def wide_view_get(
    data,
    wide_name: str,
    *,
    separator: str = "_",
    order: str = "index_then_field",
    keys=None,
    fields=None,
):
    """Get a tall-store cell via a wide column name (CIP-0010 Pattern A).

    Does not reshape ``data``. For :class:`~lynguine.assess.data.CustomDataFrame`
    uses focus ``set_index`` / ``set_column`` / ``get_value``; for a plain
    DataFrame uses label-based ``.at``.
    """
    if keys is None:
        keys = list(data.index)
    key, field = parse_wide_column_name(
        wide_name, separator=separator, order=order, keys=keys, fields=fields
    )
    if hasattr(data, "get_value") and hasattr(data, "set_index") and hasattr(data, "set_column"):
        data.set_index(key)
        data.set_column(field)
        return data.get_value()
    return data.at[key, field]


def wide_view_set(
    data,
    wide_name: str,
    value,
    *,
    separator: str = "_",
    order: str = "index_then_field",
    keys=None,
    fields=None,
):
    """Set a tall-store cell via a wide column name (CIP-0010 Pattern A).

    Does not reshape ``data``. Shape (nrows, ncols) is unchanged.
    """
    if keys is None:
        keys = list(data.index)
    key, field = parse_wide_column_name(
        wide_name, separator=separator, order=order, keys=keys, fields=fields
    )
    if hasattr(data, "set_value") and hasattr(data, "set_index") and hasattr(data, "set_column"):
        data.set_index(key)
        data.set_column(field)
        data.set_value(value)
        return data
    data.at[key, field] = value
    return data


def _nested_tall_index_column(specifications):
    """Return nested ``index`` column name for tall identity, if a string."""
    if not isinstance(specifications, dict):
        return None
    nested = specifications.get("index")
    if isinstance(nested, dict):
        nested = nested.get("name")
    if isinstance(nested, str):
        return nested
    return None


def read_wide_flatten(details):
    """
    Read a nested data source then wide-flatten to one row (CIP-0010).

    Loads ``specifications`` via ``read_data`` (so nested ``compute`` runs
    through ``finalize_data``), promotes a nested tall index when needed,
    then applies :func:`wide_flatten_dataframe`. The outer ``finalize_data``
    in :func:`read_data` may then run ``compute`` on the wide row.

    This is a **materialized snapshot** (Pattern B). For editable catalogs,
    prefer tall store + :func:`wide_view_get` / :func:`wide_view_set` (Pattern A).

    :param details: Must include ``type: wide_flatten`` and ``specifications``.
        Optional: ``separator`` (default ``_``), ``order`` (default
        ``index_then_field``), ``columns``, ``index`` (label of the singleton
        wide row — same role as wrapping ``index`` on ``stack`` / ``local``;
        omit for legacy ``0``), ``keys_field`` (default ``flattenKeys``; set
        false/null to omit). Tall identity before flatten comes from nested
        ``specifications.index`` (column promoted via ``set_index``) or from
        the nested frame's existing index.
    :type details: dict
    :return: Single-row DataFrame with index-augmented column names.
    :rtype: pandas.DataFrame
    """
    if details.get("type") != "wide_flatten":
        raise ValueError('Expected details type to be "wide_flatten".')

    if "specifications" not in details:
        raise ValueError('Details must include "specifications".')

    specs = details["specifications"]
    df, _ = read_data(details=specs)

    # Tall identity (Phase 3 / REQ-000C): nested index column, not outer index.
    tall_col = _nested_tall_index_column(specs)
    if tall_col is not None and tall_col in df.columns:
        df = df.set_index(tall_col, drop=True)

    separator = details.get("separator", "_")
    order = details.get("order", "index_then_field")
    columns = details.get("columns")
    if "keys_field" in details:
        keys_field = details["keys_field"]
        if keys_field is False:
            keys_field = None
    else:
        keys_field = "flattenKeys"

    log.debug(
        f"wide_flatten: separator={separator!r} order={order!r} "
        f"input_rows={len(df.index)} input_cols={len(df.columns)} "
        f"columns_subset={columns} keys_field={keys_field!r} "
        f"tall_index_column={tall_col!r}"
    )

    wide = wide_flatten_dataframe(
        df,
        separator=separator,
        order=order,
        columns=columns,
        keys_field=keys_field,
    )

    # Singleton result label (wrapping index); omit → legacy RangeIndex 0.
    if "index" in details:
        result_label = details["index"]
        if not isinstance(result_label, str):
            errmsg = (
                "wide_flatten wrapping index must be a string label for the "
                f"singleton wide row, got {type(result_label).__name__}."
            )
            log.error(errmsg)
            raise ValueError(errmsg)
        wide.index = pd.Index([result_label])

    log.debug(
        f"wide_flatten: output_rows={len(wide.index)} "
        f"output_cols={len(wide.columns)} "
        f"result_index={list(wide.index)!r}"
    )
    return wide


def read_data(details):
    """
    Read in the data from the details given in configuration.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read in.
    :rtype: pandas.DataFrame
    """
    if "type" in details:
        ftype = details["type"]
    else:
        raise ValueError(f'Field "type" missing in data source details for read_data, details are given as "{", ".join(details)}".')

    if ftype == "auto":
        df = read_auto(details)
    elif ftype == "stack":
        df = read_stack(details)
    elif ftype == "hstack":
        df = read_hstack(details)
    elif ftype == "vstack":
        df = read_vstack(details)
    elif ftype == "stack":
        df = read_vstack(details)
    elif ftype == "series":
        df = read_series(details)
    elif ftype == "wide_flatten":
        df = read_wide_flatten(details)
        # ``columns`` here means fields to widen, not store columns to ensure.
        # Drop flatten-only keys before finalize_data so it does not inject
        # tall names (title, complete, …) onto the wide row.  Restore wrapping
        # ``index`` on the returned interface so CustomDataFrame._finalize_df
        # still sees the singleton label (REQ-000C / CIP-0010 Phase 3).
        finalize_details = {
            k: v
            for k, v in details.items()
            if k not in ("columns", "keys_field", "order", "separator", "index")
        }
        df, finalized = finalize_data(df, finalize_details)
        if "index" in details:
            finalized["index"] = details["index"]
        return df, finalized
    elif ftype == "excel":
        df = read_excel(details)
    elif ftype == "gsheet":
        df = read_gsheet(details)
    elif ftype == "yaml":
        df = read_yaml(details)
    elif ftype == "csv":
        df = read_csv(details)
    elif ftype == "parquet":
        df = read_parquet(details)
    elif ftype == "json":
        df = read_json(details)
    elif ftype == "bibtex":
        df = read_bibtex(details)
    elif ftype == "markdown":
        df = read_markdown(details)
    elif ftype == "list":
        filelist = details.get("filename", [])
        base_dir = details.get("base_directory", "")
        if base_dir:
            filelist = [os.path.join(base_dir, f) for f in filelist]
        filelist = [confine_configured_path(f, details) for f in filelist]
        df = read_list(filelist)
    elif ftype == "yaml_directory":
        df = read_yaml_directory(details)
    elif ftype == "json_directory":
        df = read_json_directory(details)
    elif ftype == "markdown_directory":
        df = read_markdown_directory(details)
    elif ftype == "directory":
        df = read_plain_directory(details)
    elif ftype == "meta_directory":
        df = read_meta_directory(details)
    elif ftype == "bibtex_directory":
        df = read_bibtex_directory(details)
    elif ftype == "docx_directory":
        df = read_docx_directory(details)
    elif ftype == "local":
        df = read_local(details)
    elif ftype == "fake":
        df = read_fake(details)
    else:
        errmsg = f'Unknown type "{ftype}" in read_data.'
        log.error(errmsg)        
        raise ValueError(errmsg)
    return finalize_data(df, details)

def read_auto(details):
    """
    Read in the data from the details given in configuration. Use the file extension to determine the type of data to read.

    :param details: The details of the data to be read.
    :type details: dict
    :return: The data read in.
    :rtype: pandas.DataFrame
    """
    if "filename" in details:
        filename = details["filename"]
        ext = os.path.splitext(filename)[1]
        if ext == ".yaml" or ext == ".yml":
            return read_yaml(details)
        elif ext == ".json":
            return read_json(details)
        elif ext == ".csv":
            return read_csv(details)
        elif ext == ".parquet":
            return read_parquet(details)
        elif ext == ".bib" or ext == ".bibtex":
            return read_bibtex(details)
        elif ext == ".md" or ext == ".markdown":
            return read_markdown(details)
        elif ext == ".xls" or ext == ".xlsx":
            return read_excel(details)
        elif ext == ".docx":
            return read_docx(details)
    else:
        raise ValueError('Field "filename" missing in data source details for read_auto.')

def convert_data(read_details, write_details):
    """
    Convert a data set from one form to another.

    :param read_details: The details of the data to be read.
    :type read_details: dict
    :param write_details: The details of the data to be written.
    :type write_details: dict
    """
    data, details = read_data(read_details)
    write_data(data, write_details)


def data_exists(details):
    """
    Check if a particular data structure exists or needs to be created.

    :param details: The details of the data to be checked.
    :type details: dict
    :return: Whether the data exists or not.
    :rtype: bool
    """
    if "type" in details and details["type"] == "local": # this data isn't stored in a file
        return True
    if "type" in details and details["type"] == "gsheet":
        raise NotImplementedError(
            "Haven't yet implemented check for existence fo particular google sheets."
        )

    if "source" in details:
        sources = details["source"]
        available = True
        if type(sources) is not list:
            sources = [sources]
        for source in sources:
            directory = confine_configured_path(
                os.path.expandvars(source["directory"]), details
            )
            if not os.path.exists(directory):
                log.error(f'Missing directory "{directory}".')
                available = False
        return available

    if "filename" in details:
        filename = extract_full_filename(details)
        if os.path.exists(filename):
            return True
        else:
            return False
    
    else:
        log.error("Unhandled data source availability type.")
        return False


def load_or_create_df(details, index):
    """
    Load in a data frame or create it if it doesn't exist yet.

    :param details: The details of the data to be loaded or created.
    :type details: dict
    :param index: The index to be used if the data frame needs to be created.
    :type index: pandas.Index
    :return: The data frame.
    """
    if data_exists(details):
        return read_data(details)
    elif index is not None:
        log.debug(f'Creating new DataFrame from index as "{details}" is not found.')
        if "columns" in details:
            df = pd.DataFrame(index=index, columns=[index.name] + details["columns"])
            df[index.name] = index
        else:
            df = pd.DataFrame(index=index, data=index)
            df.index.name = index.name
        return finalize_data(df, details)
    else:
        raise FileNotFoundError(f'Could not find file "{extract_full_filename(details)}" and no index was provided to create it.')


def globals_data(details, index=None):
    """
    Load in the globals data to a data frame.

    :param details: The details of the data to be loaded.
    :type details: dict
    
    """
    # don't do it in the standard way as we don't want the index to be a column
    # if "index" in details:
    #     index_column_name = details["index"]
    # else:
    #     index_column_name = "index"
    # if data_exists(details):
    #     df, details = read_data(details)
    #     df.set_index(index_column_name, inplace=True)
    #     return df, details
    # elif index is not None:
    #     log.debug(f"Creating new globals DataFrame from index as \"{details}\" is not found.")
    #     if "columns" in details:
    #         df = pd.DataFrame(index=pd.Index(data=index, name=index_column_name), columns=details["columns"])
    #     else:
    #         raise ValueError(f"Field \"columns\" must be provided in globals.")
    #     return finalize_data(df, details)
    # else:
    #     raise FileNotFoundError(
    #         errno.ENOENT,
    #         os.strerror(errno.ENOENT), filename
    #         )

    return load_or_create_df(details, index)


def cache(details, index=None):
    """
    Load in the cache data to a data frame.

    :param details: The details of the data to be loaded.
    :type details: dict
    """
    return load_or_create_df(details, index)


def scores(details, index=None):
    """
    Load in the score data to data frames.

    :param details: The details of the data to be loaded.
    :type details: dict
    """
    return load_or_create_df(details, index)


def series(details, index=None):
    """
    Load in a series to data frame

    :param details: The details of the data to be loaded.
    :type details: dict
    """
    if data_exists(details):
        return read_data(details)
    elif index is not None:
        log.debug(
            f'Creating new DataFrame for write data from index as "{details}" is not found.'
        )
        return finalize_data(pd.DataFrame(index=index, data=index), details)
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), details)


def _store_index_name(details) -> str | None:
    idx = details.get("index") if isinstance(details, dict) else None
    if isinstance(idx, dict):
        return idx.get("name")
    if isinstance(idx, str):
        return idx
    return None


def _as_pandas(df) -> pd.DataFrame:
    if hasattr(df, "to_pandas"):
        return df.to_pandas()
    return df


def explode_list_field(df, field, inherit=None, index=None) -> pd.DataFrame:
    """Expand a list-of-mappings column into one row per item (CIP-0014).

    Parent columns listed in *inherit* are copied onto every child row.
    The list field itself is not kept. Child mapping keys become columns.
    """
    work = _as_pandas(df).copy()
    if work.index.name and work.index.name not in work.columns:
        work = work.reset_index()
    if field not in work.columns:
        errmsg = f'explode field "{field}" is not a column (have {list(work.columns)}).'
        log.error(errmsg)
        raise ValueError(errmsg)
    inherit = list(inherit or [])
    missing_inherit = [c for c in inherit if c not in work.columns]
    if missing_inherit:
        log.warning(
            f"explode inherit columns not present, skipping: {missing_inherit} "
            f"(have {list(work.columns)})."
        )
        inherit = [c for c in inherit if c in work.columns]

    rows = []
    for _, parent in work.iterrows():
        items = parent[field]
        if items is None or (isinstance(items, float) and pd.isna(items)):
            items = []
        elif isinstance(items, np.ndarray):
            items = items.tolist()
        if not isinstance(items, (list, tuple)):
            errmsg = (
                f'explode field "{field}" must be a list of mappings, '
                f"got {type(items).__name__}."
            )
            log.error(errmsg)
            raise ValueError(errmsg)
        parent_vals = {c: parent[c] for c in inherit}
        for item in items:
            if hasattr(item, "to_dict"):
                item = item.to_dict()
            if not isinstance(item, dict):
                errmsg = (
                    f'explode field "{field}" items must be mappings, '
                    f"got {type(item).__name__}."
                )
                log.error(errmsg)
                raise ValueError(errmsg)
            row = dict(parent_vals)
            row.update(item)
            rows.append(row)

    out = pd.DataFrame(rows)
    if index:
        if out.empty:
            if index not in out.columns:
                out[index] = pd.Series(dtype=object)
            out = out.set_index(index, drop=False)
            out.index.name = index
            return out
        if index not in out.columns:
            errmsg = f'explode index "{index}" is not a key on exploded rows.'
            log.error(errmsg)
            raise ValueError(errmsg)
        if out[index].duplicated().any():
            dups = out.loc[out[index].duplicated(), index].unique().tolist()
            errmsg = f'explode index "{index}" is not unique: {dups}.'
            log.error(errmsg)
            raise ValueError(errmsg)
        out = out.set_index(index, drop=False)
        out.index.name = index
    return out


def _packable_cell(val):
    if isinstance(val, np.ndarray):
        return val.tolist()
    if pd.isna(val) if np.ndim(val) == 0 else False:
        return val
    return val


def pack_dataframe(
    df,
    columns,
    index_value="corpus",
    index_name="Name",
    drop_incomplete=False,
    incomplete_field="embedding",
) -> pd.DataFrame:
    """Stack selected columns into one row of aligned array cells (CIP-0014)."""
    work = _as_pandas(df).copy()
    if not isinstance(columns, dict) or not columns:
        raise ValueError('pack.columns must be a mapping of dest: source.')
    if work.empty:
        packed = {dest: [[]] for dest in columns}
        idx_name = index_name or "Name"
        out = pd.DataFrame(packed, index=pd.Index([index_value], name=idx_name))
        if idx_name not in out.columns:
            out.insert(0, idx_name, index_value)
        return out
    missing = [src for src in columns.values() if src not in work.columns]
    if missing:
        errmsg = f"pack source columns not present: {missing}."
        log.error(errmsg)
        raise ValueError(errmsg)

    check = incomplete_field if incomplete_field in set(columns.values()) else None
    if check is not None:
        mask = work[check].isna()
        if mask.any() and not drop_incomplete:
            errmsg = (
                f"pack: {int(mask.sum())} row(s) missing {check}; "
                "set drop_incomplete: true to skip them."
            )
            log.error(errmsg)
            raise ValueError(errmsg)
        if drop_incomplete:
            work = work.loc[~mask]

    packed = {}
    for dest, src in columns.items():
        packed[dest] = [[_packable_cell(v) for v in work[src].tolist()]]
    idx_name = index_name or "Name"
    out = pd.DataFrame(packed, index=pd.Index([index_value], name=idx_name))
    if idx_name not in out.columns:
        out.insert(0, idx_name, index_value)
    return out


def reshape_for_write(df, details) -> pd.DataFrame:
    """Apply CIP-0014 explode / pack declared on a store, then write."""
    frame = _as_pandas(df)
    if "explode" in details:
        spec = details["explode"]
        if not isinstance(spec, dict) or "field" not in spec:
            raise ValueError('explode must be a mapping with "field".')
        frame = explode_list_field(
            frame,
            field=spec["field"],
            inherit=spec.get("inherit"),
            index=_store_index_name(details) or spec.get("index"),
        )
    if "pack" in details and isinstance(details["pack"], dict):
        spec = details["pack"]
        if "columns" not in spec:
            raise ValueError('pack must include "columns" mapping dest: source.')
        frame = pack_dataframe(
            frame,
            columns=spec["columns"],
            index_value=spec.get("index_value", "corpus"),
            index_name=_store_index_name(details) or spec.get("index_name") or "Name",
            drop_incomplete=bool(spec.get("drop_incomplete", False)),
            incomplete_field=spec.get("incomplete_field", "embedding"),
        )
    return frame


def store_stat(details) -> dict:
    """File facts for a named store without loading the table (CIP-0015)."""
    filename = extract_full_filename(details)
    logical = details.get("type")
    if not logical:
        try:
            logical = extract_file_type(filename)
        except ValueError:
            logical = None
    if logical == "parquet":
        codec = details.get("compress") or "snappy"
        if os.path.exists(filename):
            try:
                codec = parquet_codec_from_file(filename)
            except PyArrowMissingError:
                pass
    else:
        codec = resolve_text_codec(filename, details.get("compress"))
    abs_path = os.path.abspath(filename)
    if not os.path.exists(filename):
        return {
            "path": abs_path,
            "exists": False,
            "mtime": None,
            "size_bytes": 0,
            "codec": codec,
            "logical_type": logical,
            "role": details.get("role"),
        }
    st = os.stat(filename)
    mtime = datetime.fromtimestamp(st.st_mtime, tz=datetime.now().astimezone().tzinfo)
    return {
        "path": abs_path,
        "exists": True,
        "mtime": mtime.isoformat(),
        "size_bytes": st.st_size,
        "codec": codec,
        "logical_type": logical,
        "role": details.get("role"),
    }


def write_data(df, details):
    """
    Write the data using the details given in configuration.

    :param df: The data to be written.
    :type df: pandas.DataFrame or lynguine.data.CustomDataFrame
    :param details: The details of the data to be written.
    :type details: dict
    """
    if "type" in details:
        ftype = details["type"]
    else:
        log.error('Field "type" missing in data source details for write_data.')
        return

    df = reshape_for_write(df, details)

    if ftype == "excel":
        write_excel(df, details)
    elif ftype == "gsheet":
        write_gsheet(df, details)
    elif ftype == "csv":
        write_csv(df, details)
    elif ftype == "parquet":
        write_parquet(df, details)
    elif ftype == "json":
        write_json(df, details)
    elif ftype == "bibtex":
        write_bibtex(df, details)
    elif ftype == "yaml":
        write_yaml(df, details)
    elif ftype == "markdown":
        write_markdown(df, details)
    elif ftype == "yaml_directory":
        write_yaml_directory(df, details)
    elif ftype == "markdown_directory":
        write_markdown_directory(df, details)
    elif ftype == "meta_directory":
        write_meta_directory(df, details)
    else:
        errmsg = f'Unknown type "{ftype}" in write_data.'
        log.error(errmsg)
        raise ValueError(errmsg)

