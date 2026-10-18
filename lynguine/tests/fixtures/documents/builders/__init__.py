"""Synthetic PDF/DOCX builders recreating corpus layout structures (CIP-0013)."""

from .docx_layouts import make_chatbot_transcript, make_workshop_transcript
from .panel_layouts import make_cam_panel_application
from .pdf_layouts import (
    make_pmlr_twocolumn,
    make_public_dialogue_report,
    make_scan_like,
)

BUILDERS = {
    "make_public_dialogue_report": make_public_dialogue_report,
    "make_pmlr_twocolumn": make_pmlr_twocolumn,
    "make_scan_like": make_scan_like,
    "make_chatbot_transcript": make_chatbot_transcript,
    "make_workshop_transcript": make_workshop_transcript,
    "make_cam_panel_application": make_cam_panel_application,
}

__all__ = [
    "BUILDERS",
    "make_cam_panel_application",
    "make_chatbot_transcript",
    "make_pmlr_twocolumn",
    "make_public_dialogue_report",
    "make_scan_like",
    "make_workshop_transcript",
]
