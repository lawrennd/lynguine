"""High-level document → units API and compute entry point (CIP-0013)."""

from __future__ import annotations

import logging
import warnings
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from .errors import SparseTextLayerError
from .model import Document, TextLayer
from .docx_reader import read_docx
from .pdf import read_pdf
from .recogniser import StrategyCandidate, choose_strategy
from .strategy import ensure_builtin_strategies, get_strategy
from .unit import Unit

log = logging.getLogger(__name__)

OnSparse = Literal["error", "empty", "warn"]


def _attach_recogniser(units: list[Unit], choice: StrategyCandidate) -> list[Unit]:
    out: list[Unit] = []
    for u in units:
        extras = dict(u.extras or {})
        extras["recogniser_score"] = choice.score
        extras["recogniser_rationale"] = choice.rationale
        out.append(replace(u, extras=extras))
    return out


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

    if document.text_layer in (TextLayer.ABSENT, TextLayer.SPARSE):
        # Rank first so auto cannot claim a false success on empty text.
        try:
            choice = choose_strategy(document, aspect=aspect, strategy=strategy)
            strategy_id = choice.strategy_id
        except Exception:
            strategy_id = strategy if strategy != "auto" else "(unresolved)"
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

    choice = choose_strategy(document, aspect=aspect, strategy=strategy)
    strategy_id = choice.strategy_id

    strat = get_strategy(strategy_id)
    if aspect not in strat.aspects:
        raise ValueError(
            f"Strategy {strategy_id!r} does not support aspect {aspect!r} "
            f"(supports: {', '.join(strat.aspects)})"
        )
    units = strat.segment(document, **strategy_params)
    return _attach_recogniser(units, choice)


def _read_document(
    path: str,
    reader: str,
    *,
    allowed_roots: list[str] | None = None,
    details: dict[str, Any] | None = None,
):
    if reader == "pdf":
        return read_pdf(path, allowed_roots=allowed_roots, details=details)
    if reader == "docx":
        return read_docx(path, allowed_roots=allowed_roots, details=details)
    raise ValueError(f"Unsupported reader {reader!r} (expected 'pdf' or 'docx')")


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
    """Load a document (PDF or DOCX) and segment it into units."""
    document = _read_document(
        path, reader, allowed_roots=allowed_roots, details=details
    )
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


def extract_references(
    path: str,
    *,
    strategy: str = "auto",
    reader: str = "pdf",
    root: str | None = None,
    on_sparse_text: OnSparse = "error",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Compute helper: ``document_segment`` with ``aspect='references'``."""
    return document_segment(
        path,
        strategy=strategy,
        aspect="references",
        reader=reader,
        root=root,
        on_sparse_text=on_sparse_text,
        **kwargs,
    )


def extract_form_fields(
    path: str,
    *,
    strategy: str = "auto",
    reader: str = "pdf",
    root: str | None = None,
    on_sparse_text: OnSparse = "error",
    **kwargs: Any,
) -> dict[str, Any]:
    """Compute helper: return the single ``form_fields`` record as a dict.

    Segments with ``aspect='form_fields'`` and unwraps the first unit's field
    payload (one record per document). Returns ``{}`` when segmentation yields
    no units (e.g. sparse text with ``on_sparse_text='empty'``).
    """
    units = document_segment(
        path,
        strategy=strategy,
        aspect="form_fields",
        reader=reader,
        root=root,
        on_sparse_text=on_sparse_text,
        **kwargs,
    )
    if not units:
        return {}
    first = units[0]
    fields = first.get("form_fields")
    if isinstance(fields, dict):
        out = dict(fields)
    else:
        # Flat extras already merged via Unit.to_dict()
        skip = {
            "unit_id",
            "text",
            "segment_strategy",
            "aspect",
            "chunk_index",
            "word_count",
            "chunking_method",
            "was_truncated",
            "source_path",
            "recogniser_score",
            "recogniser_rationale",
            "form_fields",
        }
        out = {k: v for k, v in first.items() if k not in skip}
    out["segment_strategy"] = first.get("segment_strategy")
    if "segment_engine" in first:
        out["segment_engine"] = first["segment_engine"]
    if "recogniser_score" in first:
        out["recogniser_score"] = first["recogniser_score"]
    if "recogniser_rationale" in first:
        out["recogniser_rationale"] = first["recogniser_rationale"]
    return out
