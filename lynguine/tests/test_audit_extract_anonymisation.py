"""Tests for audit_extract_anonymisation (anonymise siding helper)."""

from lynguine.util.text import (
    audit_extract_anonymisation,
    redact_contact_pii,
    split_paragraph_units,
)


def test_audit_from_display_name_leak_without_im_in_paragraph():
    """Display-name From expects tokens even when the unit has no I'm intro."""
    raw = "Best regards,\n*Jordan Quill*\nExample Institute"
    extract = raw  # redaction missed the signature paragraph
    result = audit_extract_anonymisation(
        text=raw,
        extract_text=extract,
        sender="Jordan Quill <applicant.example@gmail.com>",
    )
    assert result["expected_name_source"] == "from_display"
    assert result["name_leak"] is True
    assert result["anonymise_ok"] is False
    # Never persist residual substrings as return values beyond flags.
    assert "Jordan" not in result.values()
    assert set(result) == {
        "name_leak",
        "email_leak",
        "phone_leak",
        "url_leak",
        "expected_name_source",
        "anonymise_ok",
    }


def test_audit_from_display_ok_when_redacted():
    raw = "Best regards,\n*Jordan Quill*\nExample Institute"
    extract = redact_contact_pii(
        raw, names=["Jordan Quill", "Jordan", "Quill"]
    )
    result = audit_extract_anonymisation(
        text=raw,
        extract_text=extract,
        sender="Jordan Quill <applicant.example@gmail.com>",
    )
    assert result["expected_name_source"] == "from_display"
    assert result["name_leak"] is False
    assert result["anonymise_ok"] is True


def test_audit_curly_im_intro_harvest():
    """Curly I’m (U+2019) must feed expected names for the audit."""
    raw = (
        "I’m Jordan Quill, a third-year undergraduate at Example Institute.\n\n"
        "I enjoy machine learning."
    )
    # Simulate a leak in a later paragraph that kept the name.
    extract = "I’m [name], a third-year undergraduate at Example Institute.\n\nJordan enjoys ML."
    result = audit_extract_anonymisation(
        text=raw,
        extract_text=extract,
        sender="applicant.example@gmail.com",
    )
    assert result["expected_name_source"] == "body_intro"
    assert result["name_leak"] is True


def test_audit_bare_from_no_intro_no_false_name_leak():
    raw = "I am interested in your research group and open projects."
    extract = raw
    result = audit_extract_anonymisation(
        text=raw,
        extract_text=extract,
        sender="applicant.example@gmail.com",
    )
    assert result["expected_name_source"] == "none"
    assert result["name_leak"] is False
    assert result["anonymise_ok"] is True


def test_audit_email_phone_url_leaks_without_storing_values():
    extract = (
        "Reach me at jordan.quill@example.com or +1-555-123-4567. "
        "Profile: https://www.linkedin.com/in/jordan-quill-example/"
    )
    result = audit_extract_anonymisation(
        text="Hello",
        extract_text=extract,
        sender="noreply@example.com",
    )
    assert result["email_leak"] is True
    assert result["phone_leak"] is True
    assert result["url_leak"] is True
    assert result["anonymise_ok"] is False
    assert "jordan.quill@example.com" not in str(result)
    assert "+1-555" not in str(result)
    assert "linkedin" not in str(result).lower() or result["url_leak"] is True


def test_audit_both_sources_and_split_units_ok_path():
    body = (
        "I’m Jordan Quill, a third-year undergraduate at Example Institute.\n\n"
        "Best regards,\n"
        "*Jordan Quill*\n"
        "Example Institute"
    )
    units = split_paragraph_units(
        text=body,
        mail_key="internship::jq",
        candidate=True,
        subject="Internship",
        sender="Jordan Quill <applicant.example@gmail.com>",
        date="2026-09-13",
        min_chars=10,
    )
    assert units
    for unit in units:
        result = audit_extract_anonymisation(
            text=unit["text"],
            extract_text=unit["extract_text"],
            sender="Jordan Quill <applicant.example@gmail.com>",
        )
        assert result["expected_name_source"] in {"from_display", "both", "body_intro"}
        assert result["name_leak"] is False
        assert result["anonymise_ok"] is True


def test_audit_accepts_from_kwarg_alias():
    result = audit_extract_anonymisation(
        text="Thanks",
        extract_text="Thanks",
        **{"from": "Jordan Quill <j@example.com>"},
    )
    assert result["expected_name_source"] == "from_display"
