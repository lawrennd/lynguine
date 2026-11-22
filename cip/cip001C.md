---
author: "Neil D. Lawrence"
created: "2026-11-22"
id: "001C"
last_updated: "2026-11-22"
status: "Proposed"
compressed: false
effort: small
priority: medium
related_requirements: ["0002"]
related_cips: []
tags:
  - cip
  - access
  - hstack
  - join
  - identifiers
  - filesystem
  - explicit-infrastructure
title: "Opt-in case-insensitive join keys on hstack / additional"
---

# CIP-001C: Opt-in case-insensitive join keys on hstack / additional

> CIPs describe HOW to achieve requirements (WHAT).  
> Implements predictable join behaviour under [REQ-0002](../requirements/req0002_predictable-architecture.md) (explicit, pandas-compatible defaults; opt-in identifier matching).

## Status

- [x] Proposed - Initial idea documented
- [ ] Accepted - Approved, ready to start work
- [ ] In Progress - Actively being implemented
- [ ] Implemented - Work complete, awaiting verification
- [ ] Closed - Verified and complete
- [ ] Rejected - Will not be implemented
- [ ] Deferred - Postponed

## Summary

Add an **opt-in, join-block** control so horizontal joins (`hstack` specifications and flow `additional` sources that join on an index/key) can match keys with Unicode case folding, while the **default remains case-sensitive** (pandas-compatible).

This is infrastructure join semantics, not a reader-specific quirk. Identifier joins (CRSId, email-like keys) and filesystem-derived indexes (directory / markdown path stems on case-insensitive volumes) both need the same contract. Referia marking flows consume the flag; they must not fork join logic.

Seeds from backlog [`2026-11-22_join-case-sensitive-flag`](../backlog/features/2026-11-22_join-case-sensitive-flag.md).

## Motivation

Joins in lynguine follow pandas: key equality is case-sensitive. That default is correct — distinct strings must not merge silently.

Identifier and path-stem joins routinely fail when orthography differs:

- Class lists store `ljt63` / `bb755` while student YAML or Moodle filenames use `LJT63` / `BB755`.
- Directory and markdown indexes often come from filenames. macOS and Windows commonly casefold; Linux often does not. The same logical file identity can disagree with a canonical lowercase roster.

IEI Worksheet 3 (2026-11-22) hit this twice: dialogues existed on disk under the right paths, but frontmatter `crsid` case broke the left join, so submissions looked missing in referia.

A `markdown_directory`-only escape hatch would teach the wrong layer and force the next similar join (Excel `additional`, CSV `hstack`, another directory type) to invent a second workaround. The flag belongs on the **join / source block**, inherited by every stackable source type.

## Detailed Description

### Design principles

1. **Default case-sensitive** — omit the flag or set the sensitive form; behaviour matches today’s `DataFrame.join` / `merge`.
2. **Opt-in on the join block** — same place as `index` / `on` / `how`, not a global lynguine setting and not buried in one reader.
3. **Match via temporary normalised keys** — prefer `str.casefold()` on copies used only for alignment. Do **not** silently rewrite the left frame’s displayed or stored index/column values unless a documented option says so.
4. **General surface** — implement in the shared hstack / join path (`read_hstack` and any helper used by flow `additional` joins) so all source types inherit it.
5. **Identifier-like keys only (guidance)** — docs recommend the flag for CRSId-like and path-stem keys, not for free text that happens to differ only by case.

### Config shape (proposed)

Prefer an extensible normaliser key over a boolean pile:

```yaml
type: hstack
specifications:
  - type: csv
    filename: data/students.csv
    # left / first source: index as today
  - type: markdown_directory
    source:
      - directory: dialogues/
        glob: "*.md"
    index: crsid
    how: left
    normalize: casefold   # opt-in; omit = case-sensitive
```

Flow `additional` blocks use the same keys:

```yaml
additional:
  - index: crsid
    type: markdown_directory
    how: left
    normalize: casefold
```

| Key | Meaning |
|-----|---------|
| *(absent)* | Case-sensitive (current behaviour) |
| `normalize: casefold` | Align on `str.casefold()` of join keys; keep left canonical values |

**Canonical API:** `normalize` (not a boolean). v1 implements only `casefold`; unknown values raise. Later normalisers (e.g. trim, or composed forms) can extend the same key without a pile of flags.

**No boolean alias in v1** — avoids two spellings in configs and docs. If sugar is wanted later, add it in a follow-up with a deprecation-safe dual accept.

### Matching algorithm (normative)

For a right source that opts in (`normalize: casefold`):

1. Determine join keys (index path or `on` columns) as today.
2. Build temporary series: `key.map(lambda x: x.casefold() if isinstance(x, str) else x)` on both sides (or equivalent vectorised path). Non-strings pass through unchanged.
3. Perform `join` / `merge` on the temporary keys.
4. Restore left-side index / `on` column values from the pre-normalised left frame (authoritative left orthography).
5. Right-side join-key columns that survive into the result follow existing suffix / earlier-wins rules; do not casefold persisted right values unless they were already the join key and dropped/replaced by left.

**Collision after casefold:** if two distinct keys on either side casefold to the same string (e.g. left `Ab` and `aB`), **raise** with an error that names the colliding raw keys and the folded form.

This is locked for lynguine v1. It is not the same policy as hstack **column** earlier-wins (overlapping column names). Casefold collision is an identity ambiguity: silent first-wins would drop or merge rows without an explicit caller choice.

**Downstream wrapper:** applications (referia) or a pre-join assess step may canonicalise or collapse keys and then join with `normalize: casefold`. That is progressive augmentation: convenience and lossy policy live above infrastructure ([REQ-0002](../requirements/req0002_predictable-architecture.md) — *“Application convenience features are implemented explicitly in application layer”*; *“Infrastructure remains pure”*).

**Missing / null keys:** unchanged from pandas (nulls do not match).

### Non-goals (v1)

- Global or environment-wide case folding.
- Mutating on-disk YAML / roster case as part of the join.
- Locale-specific case rules beyond Unicode `casefold`.
- Changing `vstack` concat semantics.
- Teaching lynguine about CRSId or Moodle; domain canonicalisation on ingest remains a complementary practice, not a substitute for the flag.

### Layering vs referia

```
lynguine read_hstack / additional join
        └── normalize: casefold  (this CIP)

referia marking configs
        └── set the flag on identifier joins; no local join fork
```

### Alternatives considered

| Approach | Why not |
|----------|---------|
| Casefold only inside `markdown_directory` | Wrong layer; Excel/CSV/path joins need the same contract |
| Always case-insensitive joins | Breaks pandas expectations; silent false merges |
| Canonicalise only on ingest | Good complementary practice; does not fix foreign keys already written in mixed case |
| Application-side pre-join mutate in referia | Violates progressive augmentation; duplicates join logic |

## Implementation Plan

1. **Contract**
   - Document `normalize` on hstack specification entries and `additional` join blocks.
   - Casefold collisions **raise** (locked); no silent first-wins in lynguine.

2. **Core helper**
   - Add a small join helper (e.g. in `lynguine/access/io.py`) that wraps index-join and column-`merge` paths used by `read_hstack`.
   - Apply only when `normalize: casefold` is set on the **right** specification being joined; left orthography preserved.

3. **Wire `additional`**
   - Ensure flow `additional` joins that share this path pick up the same key (no referia duplicate).

4. **Tests**
   - Sensitive default: `ljt63` does not match `LJT63`.
   - Opt-in: they match; left displayed key remains `ljt63` (or whichever side is left).
   - Distinct keys still distinct when sensitive.
   - Casefold collision policy as decided.
   - At least one `markdown_directory` / directory-index style fixture.

5. **Docs**
   - Update [Stacking and joining sources](../docs/getting_started/stacking.rst): optional keys table + “use for identifier-like keys” note.

## Backward Compatibility

- **Default unchanged.** Existing configs omit `normalize` and keep case-sensitive joins.
- New key is additive. Unknown values of `normalize` should raise a clear error (explicit infrastructure).
- No migration required for referia beyond opting in where identifier joins are known case-insensitive.

## Testing Strategy

- Unit tests around `read_hstack` (extend `tests/test_access_io.py` patterns).
- Fixture covering mixed-case index values with and without the flag.
- Regression: existing hstack suffix / earlier-wins tests remain green.

## Related Requirements

- [REQ-0002](../requirements/req0002_predictable-architecture.md) — predictable, explicit join behaviour; applications must not fork infrastructure joins.

Informs tenets: **explicit-infrastructure**, **authoritative-store-and-views** (left store orthography stays authoritative; normalisation is a match view).

## Implementation Status

- [ ] Accept CIP; create/refresh backlog tasks from this plan
- [ ] Join helper + `read_hstack` wiring for `normalize: casefold`
- [ ] `additional` path verified / wired if separate
- [ ] Unit tests (default, opt-in, collision policy)
- [ ] Stacking docs updated
- [ ] Link/close backlog `2026-11-22_join-case-sensitive-flag`

## References

- Backlog: [2026-11-22_join-case-sensitive-flag](../backlog/features/2026-11-22_join-case-sensitive-flag.md)
- Docs: [Stacking and joining sources](https://inverseprobability.com/lynguine/getting_started/stacking.html)
- Code: `lynguine.access.io.read_hstack`
- Trigger: IEI `_marking/worksheet3` dialogues (`crsid: "LJT63"` / `"BB755"` vs roster `ljt63` / `bb755`)
