---
id: "2026-08-13_migrate-pytest-tmpdir-to-tmp-path"
title: "Migrate legacy pytest tmpdir fixtures to tmp_path"
status: "Proposed"
priority: "Low"
created: "2026-08-13"
last_updated: "2026-08-13"
category: "infrastructure"
related_cips: []
owner: "lawrennd"
dependencies: ["2026-08-13_dependabot-pytest-bump"]
tags:
- backlog
- pytest
- tests
- technical-debt
---

# Task: Migrate legacy pytest tmpdir fixtures to tmp_path

## Description

After upgrading to pytest 9.x (`2026-08-13_dependabot-pytest-bump`), the test suite still uses
the legacy **`tmpdir` fixture** in several modules. Tests pass on pytest **9.1.1** today, but
`tmpdir` (py.path-based) is deprecated/removed in modern pytest in favour of **`tmp_path`**
(`pathlib.Path`).

Migrating reduces future breakage risk and aligns with pytest 9+ conventions.

**Do not change** uses of `tempfile.TemporaryDirectory() as tmpdir` — those are local variable
names, not the pytest fixture.

## Affected files

| File | Fixture usages |
|------|------------------|
| `lynguine/tests/test_access_io.py` | 14 test functions |
| `lynguine/tests/test_access_download.py` | `sample_settings` fixture + 2 tests |
| `lynguine/tests/test_assess_data.py` | `test_to_csv` |
| `lynguine/tests/test_util_files.py` | 2 tests |

## Acceptance Criteria

- [ ] No test function parameters named `tmpdir` (pytest fixture)
- [ ] `tmpdir.join(...)` → `tmp_path / ...`
- [ ] `str(tmpdir)` → `str(tmp_path)` or `tmp_path` as appropriate
- [ ] `sample_settings` and similar fixtures updated to accept `tmp_path`
- [ ] Full core test suite passes (`pytest lynguine/tests/ --ignore=test_server_mode.py`)
- [ ] No new pytest deprecation warnings related to tmpdir

## Implementation Notes

Mechanical migration pattern:

```python
# Before
def test_example(tmpdir):
    p = tmpdir.join("file.txt")
    p.write("content")
    fn(str(tmpdir))

# After
def test_example(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("content")
    fn(str(tmp_path))
```

For `sample_settings` in `test_access_download.py`:

```python
@pytest.fixture
def sample_settings(tmp_path):
    return Interface({
        "default_cache_path": str(tmp_path),
        ...
    })
```

Run after changes:

```bash
poetry run pytest lynguine/tests/test_access_io.py lynguine/tests/test_access_download.py \
  lynguine/tests/test_assess_data.py lynguine/tests/test_util_files.py -v
```

## Related

- Completed: `2026-08-13_dependabot-pytest-bump.md` (pytest 9.1.1 upgrade)
- pytest docs: [Temporary directories and files](https://docs.pytest.org/en/stable/how-to/tmp_path.html)

## Progress Updates

### 2026-08-13

Task created as optional follow-up after pytest 9.x upgrade. Core suite passes with legacy
`tmpdir` fixtures; migration deferred for a focused cleanup pass.
