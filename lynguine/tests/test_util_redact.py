"""RedactTerms contract and text apply (CIP-001A / REQ-0011)."""

from lynguine.util.redact import coerce_terms, placeholder_for, redact_text
from lynguine.util.text import collect_contact_pii_terms, redact_contact_pii


def test_coerce_terms_dedupes_and_longest_first():
    terms = coerce_terms(
        [
            {"value": "Ali", "kind": "name", "match": "whole_word"},
            {"value": "Ali Ghasemzadeh", "kind": "name"},
            "Ali",
            {"value": "", "kind": "email"},
        ]
    )
    assert [t["value"] for t in terms] == ["Ali Ghasemzadeh", "Ali"]
    assert terms[0]["match"] == "whole_word"


def test_redact_text_whole_word_does_not_eat_mathematics():
    text = "Mathematics candidates that help Computational work"
    out = redact_text(
        text,
        [
            {"value": "At", "kind": "name", "match": "whole_word"},
            {"value": "an", "kind": "name", "match": "whole_word"},
        ],
    )
    assert out == text
    assert "M[name]" not in out


def test_placeholder_for_kinds():
    assert placeholder_for({"value": "x", "kind": "email"}) == "[email]"
    assert placeholder_for({"value": "x", "kind": "linkedin"}) == "[linkedin]"
    assert placeholder_for({"value": "x", "kind": "other"}) == "[redacted]"


def test_collect_then_apply_matches_wrapper():
    text = (
        "Contact Ali Ghasemzadeh at ali.g@example.com "
        "or +91 99717 90675."
    )
    terms = collect_contact_pii_terms(text, names=["Ali Ghasemzadeh"])
    kinds = {t["kind"] for t in terms}
    assert "email" in kinds and "phone" in kinds and "name" in kinds
    via_terms = redact_text(text, terms)
    via_wrap = redact_contact_pii(text, names=["Ali Ghasemzadeh"])
    assert "[email]" in via_terms and "[phone]" in via_terms and "[name]" in via_terms
    assert "ali.g@example.com" not in via_terms
    assert via_terms == via_wrap
