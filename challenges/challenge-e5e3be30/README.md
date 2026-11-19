# claim-fact-verification

For each claim the case supplies, decide whether the sources support it, contradict it or cannot decide it, and show the exact passage relied on. Keep a compound claim split into its parts, do not let a literal quotation stand in for a semantic match, and record the reason for every verdict so another person can re-check it.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/quantity_audit.py` | declared number → declared source value, with named checks |
| `scripts/deliver.py` | Markdown → real DOCX/PPTX/SVG; inspect, verify, optional PDF/PNG preview |
| `MAPPING.md` | case requirement → mechanism → verification check |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | builds the synthetic data, sections and quantity plan |
| `tests/run_checks.py` | positive path plus negative paths that must be rejected |

## Requirements

Python 3.10+ and the standard library only. No network, no `pip install`, no doc-forge, no Office
suite. LibreOffice and Poppler are optional and only add a PDF/PNG preview.

## Use

```
python scripts/quantity_audit.py --plan work/quantity-plan.json --outdir work/quantity-audit
python scripts/deliver.py build-docx --md work/results.md --md work/discussion.md --out out/deliverable.docx
python scripts/deliver.py verify --out-file out/deliverable.docx --md work/results.md --outdir work/check
python scripts/deliver.py preview --docx out/deliverable.docx --outdir work/preview
```

Exit codes: `0` pass, `2` audit partial, `3` artifact verification failed.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

## Scope and limits

- The audit covers source-boundary arithmetic and prose agreement. It does not check data
  authenticity, study design, significance, causality or literature entailment.
- The DOCX writer lays out text, tables and lists; images, footnotes, equations and TOC fields
  come from a template if the case supplies one. Unlaid-out constructs are listed in the build
  report.
- Not an official score and not a substitute for review.

## Maintenance

Extend the check list, not the dependency list, and keep `tests/run_checks.py` green.
