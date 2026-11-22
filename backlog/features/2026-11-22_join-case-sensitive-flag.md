---
id: "2026-11-22_join-case-sensitive-flag"
title: "Opt-in case-insensitive join keys (default case-sensitive)"
status: "Proposed"
priority: "Medium"
created: "2026-11-22"
last_updated: "2026-11-22"
category: "features"
related_cips: ["001C"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- features
- join
- hstack
- markdown_directory
- identifiers
---

# Task: Opt-in case-insensitive join keys

> **Note**: Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements (bottom-up pattern).
> Design owned by [CIP-001C](../../cip/cip001C.md). Keep this task until Accept → split into implementation tasks if needed.

## Description

Joins in lynguine follow pandas: key matching is case-sensitive. That is the correct default (distinct strings must not merge silently). Identifier joins used by referia marking flows — especially `crsid` on `markdown_directory` / `additional` left joins — routinely fail when student YAML or Moodle filenames use `LJT63` / `BB755` while the class list has `ljt63` / `bb755`.

IEI Worksheet 3 (2026-11-22) hit this twice: dialogues were on disk under the right paths, but frontmatter `crsid` case broke the join, so submissions looked missing in referia.

Add an **opt-in** `normalize` key on join / additional source blocks (general `hstack` surface per CIP-001C). Default remains case-sensitive (omit the key). Canonical form:

```yaml
additional:
  - index: crsid
    type: markdown_directory
    how: left
    normalize: casefold
```

`normalize: casefold` is preferred over a boolean so later normalisers (e.g. trim) can extend the same key. Complementary practice (not a substitute): canonicalise identifier fields on ingest where the domain is known to be case-insensitive (Cambridge CRSid).

## Acceptance Criteria

- [ ] Join / `hstack` / `additional` source config accepts `normalize: casefold` (per CIP-001C)
- [ ] Default behaviour unchanged: case-sensitive joins (pandas-compatible)
- [ ] With `normalize: casefold`, `ljt63` matches `LJT63` / `BB755` matches `bb755` on the declared index field
- [ ] Displayed / stored index values on the left frame are not silently rewritten (match via normalised copies)
- [ ] Works for `markdown_directory` additional joins used by referia (crsid)
- [ ] Unit tests cover sensitive default, casefold opt-in, and no false merge of distinct keys when sensitive
- [ ] Docs: stacking / join page notes `normalize` and recommends it only for identifier-like keys

## Implementation Notes

- See [CIP-001C](../../cip/cip001C.md) for the full contract
- Likely touch: `lynguine/access/io.py` (`read_hstack` and shared join helper)
- Prefer temporary `str.casefold()` keys over mutating the left index in place
- Keep `normalize` on the **source / join block**, not a global lynguine setting
- referia should not fork join logic; consume the lynguine key (progressive augmentation)

## Related

- CIP: [001C](../../cip/cip001C.md)
- Trigger: IEI `_marking/worksheet3` dialogues with `crsid: "LJT63"` / `"BB755"` vs students list `ljt63` / `bb755`
- Docs: [Stacking and joining sources](https://inverseprobability.com/lynguine/getting_started/stacking.html)

## Progress Updates

### 2026-11-22

Task created (Proposed) after IEI Worksheet 3 marking join failures; design preference recorded: default case-sensitive, opt-in insensitive for identifier joins.

Linked to CIP-001C; canonical API locked as `normalize: casefold` (extensible normaliser key).
