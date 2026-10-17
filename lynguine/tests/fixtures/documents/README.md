# Document fixtures (CIP-0013)

Synthetic PDFs that **recreate layout structures** seen in real corpora, without
committing copyrighted report binaries.

| Family | Inspired by | Builder |
|--------|-------------|---------|
| `public_dialogue_report` | pub-dialogue Sciencewise-style reports; ai@cam Hopkins Van Mil reports (cover → summary → findings → recommendations → references; sparse cover page) | `builders.make_public_dialogue_report` |
| `pmlr_paper` | PMLR / mlresearch volume papers (two-column body, `References` with author–year entries) | `builders.make_pmlr_twocolumn` |
| `scan_like` | Image-only / blank pages (text-layer detection only) | `builders.make_scan_like` |

## Manifest schema

YAML under `manifests/*.yml`:

```yaml
id: public_dialogue_report_v1
family: public_dialogue_report
builder: make_public_dialogue_report
expected:
  text_layer: present          # absent | sparse | present
  min_pages: 4
  min_total_words: 200
  contains:
    - Findings
    - Recommendations
    - References
  # For later segment/reference strategies:
  # expected_strategy: pub_dialogue.v1
  # aspect: body_chunks
```

Builders run at test time (PyMuPDF required via `lynguine[documents]`). No network.

## Real corpora (local / optional)

Not committed. For manual regression against full files:

- pub-dialogue: `~/mlatcl/pub-dialogue/data/*.pdf`
- PMLR: `~/mlresearch/v*/**/*.pdf` or `assets/`
- Public downloads (examples):
  - https://www.ai.cam.ac.uk/assets/images/uploads/ai-cam-public-dialogue-report-2026.pdf
  - https://www.ai.cam.ac.uk/assets/images/uploads/ai-and-this-missions-for-government-public-dialogue-report.pdf
