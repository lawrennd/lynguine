"""Synthetic PDF builders recreating corpus layout structures (CIP-0013)."""

from .pdf_layouts import (
    make_pmlr_twocolumn,
    make_public_dialogue_report,
    make_scan_like,
)

BUILDERS = {
    "make_public_dialogue_report": make_public_dialogue_report,
    "make_pmlr_twocolumn": make_pmlr_twocolumn,
    "make_scan_like": make_scan_like,
}

__all__ = [
    "BUILDERS",
    "make_pmlr_twocolumn",
    "make_public_dialogue_report",
    "make_scan_like",
]
