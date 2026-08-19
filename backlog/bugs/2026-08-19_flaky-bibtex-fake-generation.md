---
id: "2026-08-19_flaky-bibtex-fake-generation"
title: "Fake BibTeX generation fails CI on unromanized locale names"
status: "Ready"
priority: "High"
created: "2026-08-19"
last_updated: "2026-08-19"
category: "bugs"
related_cips: []
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- bug
- fake
- bibtex
- pylatexenc
- flaky-test
---

# Task: Fake BibTeX generation fails CI on unromanized locale names

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).

## Description

`test_write_read_bibtex` failed on every Python Tests run of [PR #21](https://github.com/lawrennd/lynguine/pull/21), while the same suite passed on `main` an hour earlier. The failure is not caused by CIP-000B. It is non-deterministic fake data.

The test builds 200 random bibliography rows:

```python
row = lambda: lynguine.util.fake.to_bibtex(lynguine.util.fake.bibliography_entry())
bib_rows = lynguine.util.fake.rows(200, row)
```

`author_editor()` picks a random mimesis locale, but only romanizes Chinese, Russian, Ukrainian, Kazakh, Greek, Farsi, Japanese, and Korean. Other locales can emit characters that `pylatexenc.unicode_to_latex` cannot encode. pylatexenc 2.10 then crashes while logging its own warning:

```
TypeError: %X format: an integer is required, not str
```

CI observed:

```
FAILED lynguine/tests/test_access_io.py::test_write_read_bibtex
```

`fake.py` already has one-off mimesis data patches (`Eugen\t`, `Axel / Axl`, a short unicode-to-LaTeX map). Those do not cover the remaining locales.

## Acceptance Criteria

- [ ] `test_write_read_bibtex` is deterministic or otherwise not locale-flake-prone
- [ ] Names from any mimesis locale can pass through `to_bibtex()` without raising
- [ ] Unencodable characters are handled explicitly (romanize / ASCII-fold / drop), not by relying on pylatexenc warnings
- [ ] Existing bibtex read/write assertions still pass
- [ ] The test is run enough times locally to show the previous flake is gone

## Implementation Notes

Narrow fix in `lynguine/util/fake.py` (and the test only if a seed is added):

1. Seed the mimesis `Random` used by bibliography generation so CI is reproducible.
2. After the existing locale-specific romanization, ASCII-fold any remaining non-Latin names with `anyascii` (already a project dependency) so `unicode_to_latex` is not the backstop for Thai, Arabic, Hebrew, Hindi, and similar locales.
3. Optionally wrap `unicode_to_latex` so an unknown character cannot turn a logging warning into a `TypeError`.

Do not disable or skip `test_write_read_bibtex`. Do not couple this to the Sphinx documentation generation issues; those are a separate documentation backlog.

## Related

- PR that surfaced it: [#21](https://github.com/lawrennd/lynguine/pull/21) (CodeQL/CIP-000B; unrelated cause)
- Test: `lynguine/tests/test_access_io.py` `test_write_read_bibtex`
- Generator: `lynguine/util/fake.py` `author_editor`, `to_bibtex`, `to_bibtex_author`
- Tenet: explicit-infrastructure (generation behaviour should not depend on an unseeded locale draw)

## Progress Updates

### 2026-08-19

Task created after PR #21 CI failed four times on `test_write_read_bibtex`. Diagnosed as flaky fake-data generation, not credential hashing.
