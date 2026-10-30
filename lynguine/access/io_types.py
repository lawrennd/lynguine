"""Tabular IO type registry (CIP-0019).

Builtin ``type:`` values stay in ``read_data`` / ``write_data``. Packages
outside lynguine register extra names with ``register_io_type``. This is
the table-store sibling of CIP-0013 ``register_strategy`` (documents).

Do not import this module for its side effects from ``import lynguine``.
Entry points in group ``lynguine.io_types`` load only when a matching
``type:`` is requested and is not already registered.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from ..config.context import Context
from ..log import Logger

ctxt = Context()
log = Logger(
    name=__name__,
    level=ctxt._data["logging"]["level"],
    filename=ctxt._data["logging"]["filename"],
)

ENTRY_POINT_GROUP = "lynguine.io_types"

# Names dispatched by the builtin elif chains in io.py. Plugins cannot
# register these; v1 does not migrate builtins onto the registry.
RESERVED_IO_TYPES = frozenset(
    {
        "auto",
        "stack",
        "hstack",
        "vstack",
        "series",
        "wide_flatten",
        "excel",
        "gsheet",
        "yaml",
        "csv",
        "parquet",
        "json",
        "bibtex",
        "markdown",
        "list",
        "yaml_directory",
        "json_directory",
        "markdown_directory",
        "directory",
        "meta_directory",
        "bibtex_directory",
        "docx_directory",
        "local",
        "fake",
    }
)


class ReservedIOTypeError(ValueError):
    """Raised when a plugin tries to register a builtin ``type:`` name."""


class ReadOnlyIOTypeError(ValueError):
    """Raised when ``write_data`` is asked to write a read-only type."""


class UnknownIOTypeError(ValueError):
    """Raised when ``get_io_type`` is asked for an unregistered name."""


class PluginImportError(ValueError):
    """Raised when a ``plugins:`` module or entry point fails to load."""


@dataclass(frozen=True)
class IOType:
    """Registered tabular reader, and optional writer, for one ``type:``."""

    name: str
    read: Callable[[dict], pd.DataFrame]
    write: Callable[[pd.DataFrame, dict], None] | None = None


_REGISTRY: dict[str, IOType] = {}


def is_reserved_io_type(name: str) -> bool:
    """Return True if *name* is a lynguine builtin ``type:``."""
    return name in RESERVED_IO_TYPES


def register_io_type(name: str, *, read, write=None) -> IOType:
    """Register a tabular IO type.

    Replaces any prior plugin entry with the same *name*. Builtin names
    in ``RESERVED_IO_TYPES`` cannot be registered.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("IO type name must be a non-empty string")
    name = name.strip()
    if name in RESERVED_IO_TYPES:
        raise ReservedIOTypeError(
            f"Cannot register reserved builtin type {name!r}"
        )
    if not callable(read):
        raise TypeError(f"read for type {name!r} must be callable")
    if write is not None and not callable(write):
        raise TypeError(f"write for type {name!r} must be callable or None")
    spec = IOType(name=name, read=read, write=write)
    _REGISTRY[name] = spec
    return spec


def get_io_type(name: str) -> IOType:
    """Return the registered spec for *name*, or raise ``UnknownIOTypeError``."""
    if name not in _REGISTRY:
        raise UnknownIOTypeError(unknown_io_type_message("get_io_type", name))
    return _REGISTRY[name]


def list_io_types() -> list[str]:
    """Return registered plugin type names, sorted."""
    return sorted(_REGISTRY)


def plugins_from_mapping(mapping) -> list[str]:
    """Extract ``plugins:`` module names from a details dict or Interface."""
    if mapping is None:
        return []
    getter = getattr(mapping, "get", None)
    if getter is None:
        return []
    names = getter("plugins")
    if names is None:
        return []
    if isinstance(names, str):
        names = [names]
    else:
        try:
            names = list(names)
        except TypeError as exc:
            raise ValueError(
                f"plugins: must be a module name or a list of names, got {type(names).__name__}"
            ) from exc
    out = []
    for item in names:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"plugins: entries must be importable module names, got {item!r}"
            )
        out.append(item.strip())
    return out


def load_plugins(names, *, needed_type: str | None = None) -> None:
    """Import listed plugin modules so they can call ``register_io_type``.

    Failed imports name the module. Other exceptions from the module
    propagate unchanged.
    """
    for name in names or []:
        try:
            importlib.import_module(name)
        except ImportError as exc:
            extra = f" (needed for type {needed_type!r})" if needed_type else ""
            raise PluginImportError(
                f"Failed to import plugin module {name!r}{extra}: {exc}"
            ) from exc


def unknown_io_type_message(kind: str, ftype: str) -> str:
    """Error text for an unknown ``type:``; includes registered plugin names."""
    registered = list_io_types()
    if registered:
        extra = f" Registered plugin types: {', '.join(registered)}."
    else:
        extra = " No plugin types are registered."
    return f'Unknown type "{ftype}" in {kind}.{extra}'


def _iter_entry_points():
    """Yield ``lynguine.io_types`` entry points (empty if none)."""
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return []
    eps = entry_points()
    if hasattr(eps, "select"):
        return list(eps.select(group=ENTRY_POINT_GROUP))
    return list(eps.get(ENTRY_POINT_GROUP, []))  # type: ignore[arg-type]


def _load_entry_point(name: str) -> bool:
    """Load the entry point whose key is *name*. Return True if found."""
    for ep in _iter_entry_points():
        if ep.name != name:
            continue
        dist = getattr(ep, "dist", None)
        dist_name = getattr(dist, "name", None) or getattr(ep, "value", name)
        log.info("Loading IO type %r from entry point %s", name, dist_name)
        loaded = ep.load()
        if name not in _REGISTRY and callable(loaded):
            loaded()
        if name not in _REGISTRY:
            value = getattr(ep, "value", None)
            raise PluginImportError(
                f"Entry point {value!r} for type {name!r} did not call "
                f"register_io_type({name!r})"
            )
        return True
    return False


def resolve_registered_io_type(name: str) -> IOType | None:
    """Return a plugin spec for *name*, loading a matching entry point if needed.

    Builtin reserved names are never resolved here, even if an entry
    point claims them.
    """
    if name in RESERVED_IO_TYPES:
        return None
    if name in _REGISTRY:
        return _REGISTRY[name]
    if _load_entry_point(name):
        return _REGISTRY.get(name)
    return None


def _as_dataframe(df, ftype: str) -> pd.DataFrame:
    if isinstance(df, pd.DataFrame):
        return df
    raise TypeError(
        f"IO type {ftype!r} read() must return a pandas.DataFrame, "
        f"got {type(df).__name__}"
    )


def try_read_registered_type(details, ftype: str) -> pd.DataFrame | None:
    """Read via a plugin if *ftype* is registered. None means use builtins."""
    load_plugins(plugins_from_mapping(details), needed_type=ftype)
    spec = resolve_registered_io_type(ftype)
    if spec is None:
        return None
    return _as_dataframe(spec.read(details), ftype)


def try_write_registered_type(df: pd.DataFrame, details, ftype: str) -> bool:
    """Write via a plugin if *ftype* is registered. False means use builtins.

    A registered type never falls through to a file writer. Write still
    requires both a registered ``write`` callable and ``write: true`` on
    the item.
    """
    load_plugins(plugins_from_mapping(details), needed_type=ftype)
    spec = resolve_registered_io_type(ftype)
    if spec is None:
        return False
    if spec.write is None or not details.get("write"):
        raise ReadOnlyIOTypeError(f'Type "{ftype}" is read-only')
    spec.write(df, details)
    return True
