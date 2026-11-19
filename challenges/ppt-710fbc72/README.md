# template-aware-deck-editor

A skill for the slide tasks: a supplied PPTX template is edited (not rebuilt) — its own
placeholders are filled, its master/layout/theme stay byte-identical, every text frame is measured,
and a real preview is rendered when a renderer exists.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/edit_slides.py` | the runtime: `inspect`, `merge`, `check`, `preview` |
| `tests/validate_package.py` | independent package validator (XML, relationships, content types) |
| `MAPPING.md` | case requirement → mechanism → verification |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | builds a synthetic template deck + merge plan |
| `tests/run_checks.py` | positive path plus three negative paths |

## Requirements

Python 3.10+ and the standard library only. No network, no pip, no python-pptx. LibreOffice and
Poppler are optional and only add the PDF/PNG preview.

## Use

```
python scripts/edit_slides.py inspect /input/template.pptx --out work/deck.json
python scripts/edit_slides.py merge --deck /input/template.pptx --plan work/plan.json --outdir work/deck
python scripts/edit_slides.py check --deck /input/template.pptx --output work/deck/edited.pptx --plan work/plan.json --outdir work/deck
python scripts/edit_slides.py preview --deck work/deck/edited.pptx --outdir work/deck/preview
```

Exit codes: `0` pass, `3` a check failed. `merge` never fails silently: a missing target slide, a
missing placeholder or a missing clone source becomes a named entry in the merge report.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

Positive path: 4 placeholders filled, 1 slide added from the layout, template parts byte-identical,
8/8 checks pass, and the independent validator accepts the package. Negative paths: a plan naming
a non-existent slide, a plan naming a placeholder the layout lacks, and a body that overflows its
own box must each be reported.

## Scope and limits

- The editor fills placeholders and clones layout-shaped slides. It does not add pictures, charts,
  SmartArt, transitions or speaker notes; a case that needs them must supply a template slide that
  already contains them (clone it) or the agent must add them with a real tool.
- The overflow figure is an **estimate** from character count, font size and frame width. The
  rendered preview is the visual check; a long unbroken token can still overflow without tripping
  the estimate.
- Placeholder inheritance is preserved by construction (slides point at real layouts; master,
  layouts and theme are copied byte-for-byte). The editor does not remap a case's template onto a
  different template.
- Not an official score; the checks prove template fidelity and declared-content presence, not
  scientific judgement about the deck's storyline.

## Maintenance

One standard-library script plus an independent validator. Extend the checks and the merge
operations, not the dependency list, and keep `tests/run_checks.py` green — including its three
negative paths.
