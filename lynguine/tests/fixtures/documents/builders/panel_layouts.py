"""Synthetic Cambridge Panel–like PG application PDFs (no real PII).

Layout mimics department-copy header + Personal Information/Contact +
Referee Details with decoy referee emails — for CIP-0013 form_fields tests.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def make_cam_panel_application(path: str | Path) -> Path:
    """Build a small multi-page Panel-shaped application PDF.

    Uses only synthetic names, USNs, and emails.
    """
    path = Path(path)
    doc = fitz.open()

    page0 = doc.new_page()
    page0.insert_textbox(
        fitz.Rect(50, 40, 550, 780),
        "\n".join(
            [
                "Postgraduate Application Form",
                "Department Copy",
                "SMITH, Ms Jane ANN",
                "Application Number: 90000001",
                "USN: 90000002",
                "PhD in Synthetic Computing (SC01)",
                "Date submitted 21 Sept 2026",
                "Mode of study Full-time",
                "Course start date 04 Oct 2027 (MT 2027)",
                "Nationality United Kingdom",
                "Estimated fee status Home",
                "SMITH, Ms Jane ANN",
            ]
        ),
        fontsize=10,
    )

    contact = doc.new_page()
    contact.insert_textbox(
        fitz.Rect(50, 40, 550, 780),
        "\n".join(
            [
                "Personal Information",
                "Contact",
                "Email jane.ann.smith@example.com",
                "Contact address 1 Synthetic Street",
                "Cambridge",
                "CB1 1AA",
                "United Kingdom",
                "Phone 01223 000000",
                "Valid until 01 Jan 2028",
                "Home address",
                "Somewhere Else",
                "Immigration",
                "Language",
                "Funding",
                "Referee Details",
                "Referee One",
                "Email referee.one@university.example",
                "Referee Details",
                "Referee Two",
                "Email referee.two@college.example",
                "Research",
                "Statement body text for fixture only.",
            ]
        ),
        fontsize=10,
    )

    doc.save(path)
    doc.close()
    return path
