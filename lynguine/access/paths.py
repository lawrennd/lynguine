"""Explicit path confinement for lynguine's access flow (CIP-000A).

Configured or caller-supplied paths are resolved and required to sit
under one or more allowed roots. Primitive I/O helpers do not use this
module; they remain trusted-caller APIs.
"""

from __future__ import annotations

import os
from typing import Iterable, Sequence


class _DefaultRootsType:
    """Sentinel: caller omitted allowed_roots; use the flow directory."""

    def __repr__(self) -> str:
        return "DEFAULT_ROOTS"


DEFAULT_ROOTS = _DefaultRootsType()


class PathEscapeError(ValueError):
    """Raised when a path is not under any allowed root."""

    def __init__(self, path: str | None, roots: Sequence[str]):
        self.path = path
        self.roots = list(roots)
        super().__init__(
            f"Path {path!r} is not under allowed roots {self.roots!r}"
        )


def _realpath(path: str) -> str:
    return os.path.realpath(os.path.expanduser(os.path.expandvars(path)))


def effective_roots(directory: str, allowed_roots=DEFAULT_ROOTS, unbounded_paths: bool = False):
    """Return ``(roots, unbounded)`` for a flow entry point.

    ``allowed_roots is None`` or ``unbounded_paths=True`` is the explicit
    opt-out. Omitting roots (the ``DEFAULT_ROOTS`` sentinel) uses
    ``directory`` as the single jail.
    """
    if unbounded_paths or allowed_roots is None:
        return None, True
    if allowed_roots is DEFAULT_ROOTS:
        if not directory:
            raise PathEscapeError(directory, [])
        return [_realpath(directory)], False
    return [str(root) for root in allowed_roots], False


def confine_configured_path(path: str, details: dict | None) -> str:
    """Resolve ``path`` under ``details['allowed_roots']`` when present.

    Interface YAML cannot enlarge the jail: ``from_flow`` overwrites
    ``allowed_roots`` / ``unbounded_paths`` on each item from the Interface
    object, not from the YAML dict.
    """
    if not details:
        return path
    if details.get("unbounded_paths"):
        return path
    roots = details.get("allowed_roots")
    if roots:
        return resolve_under_roots(path, roots)
    return path


def resolve_under_roots(path: str, roots: Iterable[str]) -> str:
    """Expand, resolve, and require ``path`` to sit under one of ``roots``.

    The caller passes ``roots``; there is no process-global default.

    :param path: Path to resolve (relative or absolute)
    :type path: str
    :param roots: Allowed root directories
    :type roots: Iterable[str]
    :return: Real path of ``path``
    :rtype: str
    :raises PathEscapeError: If the path is empty, contains NUL, roots are
        empty, or the resolved path is not under any root
    """
    root_list = [root for root in roots if root]
    if path is None or path == "" or "\x00" in str(path):
        raise PathEscapeError(path, root_list)
    if not root_list:
        raise PathEscapeError(path, root_list)

    resolved = _realpath(path)
    for root in root_list:
        resolved_root = _realpath(root)
        if resolved == resolved_root or resolved.startswith(resolved_root + os.sep):
            return resolved
    raise PathEscapeError(path, root_list)
