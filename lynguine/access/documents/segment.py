"""High-level document → units API and compute entry point (CIP-0013)."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from .errors import SparseTextLayerError
from .model import Document, TextLayer
from .pdf import read_pdf
from .strategy import ensure_builtin_strategies, get_strategy, resolve_strategy_id
from .unit import Unit

log = logging.getLogger(__name__)

OnSparse = Literal["error", "empty", "warn"]


def segment_document(
    document: Document,
    *,
    strategy: str = "auto",
    aspect: str = "body_chunks",
    on_sparse_text: OnSparse = "error",
    **strategy_params: Any,
) -> list[Unit]:
    """Segment an already-loaded :class:`Document` into units."""
    ensure_builtin_strategies()
    strategy_id = resolve_strategy_id(strategy, aspect=aspect)

    if document.text_layer in (TextLayer.ABSENT, TextLayer.SPARSE):
        msg = (
            f"Document {document.path!r} has text_layer={document.text_layer.value!r} "
            f"(words_per_page={document.words_per_page:.1f}); "
            f"strategy {strategy_id!r} requires extractable text. "
            "OCR is out of scope for CIP-0013 v1."
        )
        if on_sparse_text == "error":
            raise SparseTextLayerError(msg)
        if on_sparse_text == "warn":
            warnings.warn(msg, UserWarning, stacklevel=2)
            log.warning(msg)
        else:
            log.warning(msg)
        return []

    strat = get_strategy(strategy_id)
    if aspect not in strat.aspects:
        raise ValueError(
            f"Strategy {strategy_id!r} does not support aspect {aspect!r} "
            f"(supports: {', '.join(strat.aspects)})"
        )
    return strat.segment(document, **strategy_params)


def segment_pdf(
    path: str,
    *,
    strategy: str = "auto",
    aspect: str = "body_chunks",
    reader: str = "pdf",
    allowed_roots: list[str] | None = None,
    details: dict[str, Any] | None = None,
    on_sparse_text: OnSparse = "error",
    **strategy_params: Any,
) -> list[Unit]:
    """Load a PDF and segment it into units."""
    if reader != "pdf":
        raise ValueError(f"Unsupported reader {reader!r} (only 'pdf' in this task)")
    document = read_pdf(path, allowed_roots=allowed_roots, details=details)
    return segment_document(
        document,
        strategy=strategy,
        aspect=aspect,
        on_sparse_text=on_sparse_text,
        **strategy_params,
    )


def units_to_frame(units: list[Unit]) -> pd.DataFrame:
    """Explode units to one row per unit (CIP-0013 default grain)."""
    if not units:
        return pd.DataFrame(
            columns=[
                "unit_id",
                "text",
                "segment_strategy",
                "aspect",
                "chunk_index",
                "word_count",
                "chunking_method",
                "was_truncated",
                "source_path",
            ]
        )
    df = pd.DataFrame([u.to_dict() for u in units])
    if "unit_id" in df.columns:
        df = df.set_index("unit_id", drop=False)
    return df


def segment_pdf_frame(path: str, **kwargs: Any) -> pd.DataFrame:
    """Load, segment, and return an exploded DataFrame of units."""
    return units_to_frame(segment_pdf(path, **kwargs))


def document_segment(
    path: str,
    *,
    strategy: str = "auto",
    aspect: str = "body_chunks",
    reader: str = "pdf",
    root: str | None = None,
    on_sparse_text: OnSparse = "error",
    min_chunk_words: int | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Compute-registry entry: return unit dicts for the current row's path.

    YAML sketch::

        compute:
          - function: document_segment
            field: units
            row_args:
              path: filename
            args:
              strategy: pub_dialogue.v1
              aspect: body_chunks
              root: data

    For exploded tables use :func:`segment_pdf_frame` outside per-row compute.
    """
    allowed_roots = None
    if root is not None:
        allowed_roots = [str(Path(root).expanduser().resolve())]
        # If path is relative, join under root
        p = Path(path)
        if not p.is_absolute():
            path = str(Path(root) / p)

    params = dict(kwargs)
    if min_chunk_words is not None:
        params["min_chunk_words"] = min_chunk_words

    units = segment_pdf(
        path,
        strategy=strategy,
        aspect=aspect,
        reader=reader,
        allowed_roots=allowed_roots,
        on_sparse_text=on_sparse_text,
        **params,
    )
    return [u.to_dict() for u in units]
