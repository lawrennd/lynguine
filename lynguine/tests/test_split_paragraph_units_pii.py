"""Paragraph units: listing title + PII scrub for extract_text."""

from lynguine.util.text import (
    names_from_sender,
    redact_contact_pii,
    split_paragraph_units,
)


def test_names_from_sender():
    names = names_from_sender("Ali Ghasemzadeh <ali@sharif.edu>")
    assert "Ali Ghasemzadeh" in names
    assert "Ali" in names and "Ghasemzadeh" in names
    assert "Ze Chen" in names_from_sender('"Chen, Ze" <ze@example.com>')


def test_redact_contact_pii_email_phone_name():
    text = (
        "Contact Ali Ghasemzadeh at ali.g@example.com "
        "or +91 99717 90675."
    )
    out = redact_contact_pii(text, names=["Ali Ghasemzadeh"])
    assert "ali.g@example.com" not in out
    assert "[email]" in out
    assert "[phone]" in out
    assert "99717" not in out
    assert "[name]" in out
    assert "2027" in redact_contact_pii("Fall 2027 intake")


def test_split_paragraph_units_title_and_redacted_extract():
    body = (
        "I'm Ali Ghasemzadeh, a final-year student.\n\n"
        "Email me at ali.g@example.com or +91 9971790675.\n\n"
        "My name is Samarth Kumar and I study ML."
    )
    units = split_paragraph_units(
        text=body,
        mail_key="phd::abc",
        candidate=True,
        subject="PhD Inquiry – Fall 2027",
        sender="Ali Ghasemzadeh <ali@sharif.edu>",
        date="2026-10-01",
        min_chars=20,
    )
    assert len(units) == 3
    assert units[0]["title"] == "PhD Inquiry – Fall 2027 · ¶1"
    assert units[0]["description"].startswith("Ali Ghasemzadeh")
    assert units[0]["date"] == "2026-10-01"
    assert "Ali Ghasemzadeh" in units[0]["text"]
    assert "Ali Ghasemzadeh" not in units[0]["extract_text"]
    assert "I'm [name]" in units[0]["extract_text"] or "I'M [name]" in units[0]["extract_text"]
    joined = " ".join(u["extract_text"] for u in units)
    assert "[email]" in joined
    assert "[phone]" in joined
    assert "ali.g@example.com" not in joined
    assert "my name is [name]" in joined.lower()


def test_split_redacts_body_name_when_from_is_bare_email():
    body = "I'm Ali Ghasemzadeh, a final-year Computer Engineering student."
    units = split_paragraph_units(
        text=body,
        mail_key="phd::x",
        candidate=True,
        subject="PhD Inquiry",
        sender="lyqasmzadh72@gmail.com",
        date="2026-11-05",
        min_chars=20,
    )
    assert len(units) == 1
    assert units[0]["description"] == "lyqasmzadh72@gmail.com"
    assert "Ali Ghasemzadeh" not in units[0]["extract_text"]
    assert "[name]" in units[0]["extract_text"]


def test_split_redacts_unicode_im_and_markdown_signature():
    """Mail often uses I’m (U+2019); signature may be *Name* with bare From."""
    body = (
        "I’m Aayaann Kausar, a third-year undergraduate at IIT Kharagpur.\n\n"
        "Best regards,\n"
        "*Aayaann Kausar*\n"
        "IIT Kharagpur"
    )
    units = split_paragraph_units(
        text=body,
        mail_key="internship::ak",
        candidate=True,
        subject="IIT Kharagpur — AI Research Internship Inquiry",
        sender="aayaannkausar@gmail.com",
        date="2026-09-13",
        min_chars=10,
    )
    assert len(units) >= 2
    joined = "\n".join(u["extract_text"] for u in units)
    assert "Aayaann" not in joined
    assert "Kausar" not in joined
    assert "[name]" in joined
    # Listing text keeps the raw body; only extract_text is scrubbed.
    assert any("Aayaann Kausar" in u["text"] for u in units)


def test_redact_does_not_eat_at_inside_words():
    """Regression: short crumbs like 'at' must not destroy Mathematics."""
    para = (
        "My background is in problem solving. I qualified for the Indian "
        "Olympiad Qualifier in Mathematics, ranked 898 in JEE Advanced out of "
        "roughly 1.5 million candidates, and hold the highest CGPA in my "
        "department (9.412/10) of Engineering and Computational Mechanics. I "
        "know I am at an early stage as a researcher, and I am prepared to "
        "work hard to make full use of an opportunity like this: to read the "
        "papers your group builds on, learn the tools it uses, and take on "
        "any task that helps the project."
    )
    # Simulate a bad short name slipping in, plus a real person name.
    out = redact_contact_pii(para, names=["At", "an", "Samarth Kumar"])
    assert "Mathematics" in out
    assert "candidates" in out
    assert "Computational" in out
    assert "that helps" in out
    assert "I am at an early stage" in out
    assert "M[name]hem" not in out
    assert "candid[name]" not in out


def test_bare_email_sender_does_not_yield_local_part_name():
    assert names_from_sender("at@gmail.com") == []
    assert names_from_sender("lyqasmzadh72@gmail.com") == []


def test_redact_profile_and_personal_urls():
    text = (
        "Links: [Scholar](https://scholar.google.com/citations?user=xx9fMxYAAAAJ&hl=en) "
        "https://www.linkedin.com/in/wasswa-shafik-3a129b220/ "
        "GitHub: https://github.com/Atharva6907 "
        "Code: https://github.com/ehsankmi/EVT-MARL "
        "ORCID: https://orcid.org/0009-0002-6637-6134 "
        "X: https://x.com/lawrennd "
        "Twitter: https://twitter.com/lawrennd "
        "Website: https://www.bdu.edu.et/fc/index.php/node/323 "
        "and a paper link https://arxiv.org/abs/1234.5678 stays."
    )
    out = redact_contact_pii(text)
    assert "linkedin.com" not in out.lower()
    assert "scholar.google" not in out.lower()
    assert "github.com/Atharva6907" not in out
    assert "github.com/ehsankmi" not in out
    assert "orcid.org" not in out.lower()
    assert "x.com/lawrennd" not in out.lower()
    assert "twitter.com/lawrennd" not in out.lower()
    assert "[linkedin]" in out
    assert "[scholar]" in out
    assert "[github]" in out
    assert "[orcid]" in out
    assert "[twitter]" in out
    assert "[website]" in out
    assert "arxiv.org/abs/1234.5678" in out
