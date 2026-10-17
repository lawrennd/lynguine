"""Errors for document access (CIP-0013)."""


class DocumentSegmentError(ValueError):
    """Base error for document segmentation failures."""


class SparseTextLayerError(DocumentSegmentError):
    """Raised when a strategy needs a text layer but the PDF is absent/sparse."""


class UnknownStrategyError(DocumentSegmentError):
    """Raised when a strategy id is not registered."""
