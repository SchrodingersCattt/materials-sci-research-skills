# source-faithful-template-adaptation

A skill for the academic format/template adaptation topic: a supplied manuscript is brought
to a supplied template with the template's own specification extracted, applied and verified
item by item, and with the manuscript's content left intact.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first: contract, workflow, failure handling |
| `scripts/adapt_template.py` | the whole runtime: `inspect`, `specify`, `apply`, `verify`, `preview` |
| `MAPPING.md` | requirement direction → mechanism → verification check |
| `PROVENANCE.md` | origin, hashes, dependency and boundary statement |
| `examples/synthetic_case.py` | builds a synthetic template/manuscript DOCX pair for self-testing |
| `tests/run_checks.py` | runs the pipeline on that pair and on refusal paths, and prints a verdict |

## Requirements

- Python 3.10 or newer. **Standard library only** (`zipfile`, `xml.etree`, `json`,
  `hashlib`, `subprocess`). No network access, no `pip install`, no doc-forge, no Office
  suite is needed for `inspect` / `specify` / `apply` / `verify`.
- Optional: LibreOffice (`soffice`) plus Poppler (`pdftoppm`, `pdffonts`, `pdftotext`) for a
  genuine PDF/PNG preview and a font report. When they are absent the preview step records
  the missing renderer and the editable DOCX remains the deliverable.

## Use

```
python scripts/adapt_template.py inspect  <file>    --out /app/work/inspect.json
python scripts/adapt_template.py specify  --template <template.docx> --source <manuscript.docx> --out /app/work/spec.json
python scripts/adapt_template.py apply    --source <manuscript.docx> --template <template.docx> --spec /app/work/spec.json --outdir /app/work/adapted
python scripts/adapt_template.py verify   --source <manuscript.docx> --output /app/work/adapted/adapted.docx --spec /app/work/spec.json --outdir /app/work/adapted
python scripts/adapt_template.py preview  --docx /app/work/adapted/adapted.docx --outdir /app/work/adapted
```

Exit codes: `0` success, `2` refused adaptation (read `reason` in `apply-report.json`),
`3` verification found failing checks (read `verification.json`). A refusal and a failing
check are results, not crashes: report them.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

`tests/run_checks.py` builds the synthetic pair, runs specify/apply/verify, asserts the
content stream is preserved, asserts every check passes on the fixture, and asserts that a
non-DOCX template is refused instead of silently guessed.

## Scope and limits

- DOCX→DOCX adaptation is fully supported. A PDF, LaTeX or prose-only template has no style
  definitions to import: the stated rules (page setup, font, size, spacing, caption
  position, reference style) are applied where the format allows, and everything else is
  reported as unchecked.
- Numbering, cross-reference fields, TOC fields, headers/footers and journal front matter
  are preserved from the manuscript rather than regenerated; a case that requires the
  template's own numbering, headers or front matter needs an explicit, recorded decision.
- Style roles are inferred from style names, outline levels and template structure. An
  unusual template may need an explicit mapping override, which must be recorded as such.
- The verification proves geometry, style application, content preservation and package
  integrity. It does not certify typographic beauty, scientific meaning or any official
  score.

## Maintenance

Single-file runtime with no third-party imports: keep it that way and extend the check list
rather than the dependency list. Any change to `adapt_template.py` must keep
`tests/run_checks.py` green, including the fixture values it asserts.
