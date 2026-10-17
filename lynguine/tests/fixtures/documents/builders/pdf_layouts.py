"""Generate small PDFs that mimic public-dialogue reports and PMLR papers.

Structures observed (2026-10-17) from local pub-dialogue data/, mlresearch
volumes, and public ai@cam reports — recreated synthetically for CI.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def _para(n: int, prefix: str = "Text") -> str:
    return " ".join(f"{prefix}{i}" for i in range(n))


def make_scan_like(path: str | Path, *, pages: int = 2) -> Path:
    """Blank pages → text_layer absent (detection only; no OCR)."""
    path = Path(path)
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    doc.save(path)
    doc.close()
    return path


def make_public_dialogue_report(path: str | Path) -> Path:
    """Single-column report shaped like Sciencewise / ai@cam dialogue PDFs.

    Observed pattern: sparse cover (title/nav), then denser body with
    Findings / Recommendations / References. Not a copy of any real report.
    """
    path = Path(path)
    doc = fitz.open()

    # Cover — few words (real ai@cam local-gov cover ~20 words)
    cover = doc.new_page()
    cover.insert_textbox(
        fitz.Rect(72, 200, 520, 400),
        "Public Dialogue on Emerging Technology\nSynthetic fixture — not a real report",
        fontsize=16,
        align=fitz.TEXT_ALIGN_CENTER,
    )

    # Contents / summary
    summary = doc.new_page()
    summary.insert_textbox(
        fitz.Rect(72, 72, 520, 750),
        "Summary\n\n"
        "Participants discussed benefits and concerns about new technology "
        "in public services. " + _para(50, "summary"),
        fontsize=11,
    )

    # Findings (body)
    findings = doc.new_page()
    findings.insert_textbox(
        fitz.Rect(72, 72, 520, 750),
        "Findings\n\n"
        "Members of the public raised concerns about accountability and "
        "transparency when systems make decisions that affect them. "
        + _para(60, "finding"),
        fontsize=11,
    )

    # Recommendations
    recs = doc.new_page()
    recs.insert_textbox(
        fitz.Rect(72, 72, 520, 750),
        "Recommendations\n\n"
        "Dialogue participants recommended clear human oversight and "
        "published criteria for when automated tools may be used. "
        + _para(50, "rec"),
        fontsize=11,
    )

    # References (prose list — report style, not PMLR two-column)
    refs = doc.new_page()
    refs.insert_textbox(
        fitz.Rect(72, 72, 520, 750),
        "References\n\n"
        "Hopkins Van Mil (2024). AI and the Missions for Government: "
        "insights from a public dialogue.\n\n"
        "Sciencewise (2022). NHS AI Lab Public Dialogue on Data Stewardship.\n\n"
        "Royal Society (2004). Nanoscience and nanotechnologies: "
        "opportunities and uncertainties.\n",
        fontsize=10,
    )

    doc.save(path)
    doc.close()
    return path


def make_pmlr_twocolumn(path: str | Path) -> Path:
    """Two-column academic paper with a References section (PMLR-like).

    Real PMLR PDFs show median block width ~0.45–0.65 of page width and a
    clear References heading with author–year entries. This fixture places
    two text columns on the body page, then a references page.
    """
    path = Path(path)
    doc = fitz.open()
    page = doc.new_page()  # A4-ish default

    # Title band (full width)
    page.insert_textbox(
        fitz.Rect(72, 48, 520, 100),
        "Synthetic Proceedings Paper Title\nA. Author and B. Writer",
        fontsize=12,
        align=fitz.TEXT_ALIGN_CENTER,
    )

    left = (
        "Abstract. We study a synthetic problem for layout testing. "
        + _para(40, "L")
        + "\n\n1 Introduction\n\n"
        + _para(45, "intro")
    )
    right = (
        "2 Method\n\n"
        + _para(40, "method")
        + "\n\n3 Experiments\n\n"
        + _para(40, "exp")
    )
    page.insert_textbox(fitz.Rect(54, 110, 290, 780), left, fontsize=9)
    page.insert_textbox(fitz.Rect(305, 110, 541, 780), right, fontsize=9)

    ref_page = doc.new_page()
    ref_page.insert_textbox(
        fitz.Rect(54, 72, 541, 780),
        "References\n\n"
        "Faruk Ahmed and Aaron Courville. Detecting semantic anomalies. "
        "In AAAI, pp. 3154–3162, 2020.\n\n"
        "Stafford Beer. Brain of the Firm. Allen Lane, 1972.\n\n"
        "Roger C. Conant and W. Ross Ashby. Every good regulator of a system "
        "must be a model of that system. Int. J. Systems Sci., 1970.\n\n"
        "Yann LeCun, Yoshua Bengio, and Geoffrey Hinton. Deep learning. "
        "Nature, 521:436–444, 2015.\n",
        fontsize=9,
    )

    doc.save(path)
    doc.close()
    return path
