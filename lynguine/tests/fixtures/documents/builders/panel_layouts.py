"""Synthetic form-layout PDFs for CIP-0013 form_fields tests (no real PII).

Includes Cambridge Panel department-copy header/contact/referees, and a
labelled consecutive-line (key then value) grant form.
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


def make_labeled_kv_form(path: str | Path) -> Path:
    """Build a labelled consecutive-line grant-form PDF.

    Uses only synthetic names and emails. Includes an abstract line that
    extraction must not pull into form fields.
    """
    path = Path(path)
    doc = fitz.open()

    page0 = doc.new_page()
    page0.insert_textbox(
        fitz.Rect(50, 40, 550, 780),
        "\n".join(
            [
                "Visiting Professorship",
                "Applicant: Professor Ada Host",
                "ID/Ref: VP2-2099-001",
                "Project Title: Visiting Professorship - Dr Visitor One",
                "Submission Date: 01 September 2026",
                "Total Requested: £13,999",
                "Host Applicant Details",
                "Title",
                "Professor",
                "First Name",
                "Ada",
                "Last Name",
                "Host",
                "Institution",
                "Example College London",
                "Department",
                "Department of Synthetic Computing",
                "Position",
                "Professor",
                "Address",
                "1 Synthetic Street",
                "London",
                "SW7 2AZ",
                "Email Address",
                "ada.host@example.ac.uk",
                "Telephone No.",
                "+44 20 0000 0000",
                "Visiting Professor Details",
                "Title",
                "Dr",
                "First Name",
                "Visitor",
                "Last Name",
                "One",
                "Honours",
                "Gender",
                "Date of Birth",
                "01/01/2099",
                "Institution",
                "Example State University",
                "Address",
                "Department",
                "School of Electrical,",
                "Computer and Energy Engineering",
                "Telephone No.",
                "+1 000 000 0000",
                "Email Address",
                "visitor.one@example.edu",
                "Visiting Professor CV",
                "Synthetic CV heading only.",
            ]
        ),
        fontsize=10,
    )

    page1 = doc.new_page()
    page1.insert_textbox(
        fitz.Rect(50, 40, 550, 780),
        "\n".join(
            [
                "Programme Summary",
                "Total number of months",
                "3",
                "Number of visits",
                "1",
                "Please add an entry for each planned visit with dates where known.",
                "CONFIDENTIAL_PHRASE_SHOULD_NOT_LEAK",
                "Programme Outline",
                "Advice with host staff.",
            ]
        ),
        fontsize=10,
    )

    doc.save(path)
    doc.close()
    return path
