---
name: terminology-consistent-literature-translation
description: |-
  Use when a scientific paper must be translated while staying verifiable: a glossary pinned across the whole document, paragraph-aligned bilingual output, and citations, formulas and numeric values carried through unchanged.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan            # contract, check list, result.json skeleton
# ... read the case material and write the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md
```

`plan` takes no reading of its own. `finish` returns a JSON report whose `failed_checks` names exactly
what to repair, and exits non-zero if a stage failed or a placeholder is still in `result.json`.

## Budget order (do this first)

1. **Produce the deliverable now**, in the container format the case asks for, even if some fields are
   still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rebuild, verify, update `result.json`.
   Never let step 3 exhaust the budget before step 1 has happened.


## Contract

- Read the real `/input/case.json` and `task.md` and every material they reference, including
  `environment/resources.yaml`. Read the actual files; a filename or a discipline label is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Produce a located, useful
  deliverable early and refine it; do not spend the budget on prose about method.
- Standard library only. No network. Declared tools include `pdf-text-tool`, `pdf-render-tool`,
  `ocr-tool`, `latex-compiler`, `office-renderer` and `scientific-python`.
- Skill resources are capped at 50 UTF-8 text files, 500 KB each, 2 MB total, no symlinks.


# 文献翻译 — translate a paper while keeping it verifiable

## Engine

`scripts/reading_contract.py` — read the case's contract, then prove the answer satisfies it while every
value stays traceable to a span of the material.

```bash
python "$SKILL_DIR/scripts/reading_contract.py" contract --case /input/case.json --out work/contract.json
# ... produce work/answer.md from the material ...
python "$SKILL_DIR/scripts/reading_contract.py" check --answer work/answer.md --case /input/case.json     --outdir work/check
python "$SKILL_DIR/scripts/reading_contract.py" verify --answer work/answer.md --outdir work/check
```

1. **`contract`** reads `/input/case.json` and reports the fields and questions the case actually asks
   for. Use it to drive the answer instead of guessing the field set. `--fields` and `--questions`
   accept explicit overrides when the case states them in prose rather than in the contract.
2. **`check`** compares the answer against the contract: which required fields are present, which are
   missing, which carry no locator, and which values cannot be found in the material. It writes its
   report under `--outdir` and names what to repair.
3. **`verify`** re-runs the conformance proof over the repaired answer and exits non-zero while any
   required item is still unresolved.

Read the case's own material with the declared tools (`pdf-text-tool`, `pdf-render-tool`,
`ocr-tool`); the engine does not read PDFs for you, it checks what you extracted.


## What this must get right

- Values are quoted from the material, not paraphrased into them. Units, error terms and statistical
  quantities are carried with the value, not normalised or converted.
- Reading order for multi-column input is resolved before anything is extracted, and the resolved order
  is recorded, because a wrong reading order corrupts every downstream field.
- Complex tables are read by row and column with merged cells reported as merged, not silently
  duplicated or dropped.
- A conclusion, a limitation and a speculative statement are distinguished. Hedged wording
  (`may`, `suggest`, `提示`, `可能`) is quoted with its hedge intact and never promoted to a finding.
- Every extracted field can be traced to a page, paragraph, table row and column, or figure caption.
- **One glossary, applied everywhere.** The same source term gets the same target term in every
  occurrence; a term that appears once is still recorded, so a later pass cannot drift.
- **Paragraph alignment is exact.** Every target paragraph maps to exactly one source paragraph, and
  the mapping is emitted so a reviewer can compare side by side.
- **Citations, formulas, units and numeric values are copied through byte-for-byte.** They are never
  translated, reformatted, or renumbered.
- **The translation does not add or remove claims.** A sentence with no counterpart in the source is a
  defect, and so is a source sentence with no counterpart in the output.


## What it must refuse

- **Refuse to invent a locator.** If a value cannot be bound to a span, report it as unresolved rather
  than attaching a plausible-looking reference.
- **Refuse to fill a gap.** Material that does not report a field yields `not reported`, never a
  plausible value, an interpolated one, or a "typically" figure.
- **Refuse to treat absence as evidence.** A field not reported is not evidence that the underlying
  thing was not measured.
- **Refuse to pass OCR noise as content.** If a text layer is missing or garbled, say so and report the
  affected region; do not smooth it into readable text.
- **Refuse to translate a citation key or a formula.** Those are identifiers, not prose.
- **Refuse to silently drop a passage.** Untranslatable content is reported as untranslated with its
  locator, never omitted.


## Evidence you can reproduce

Use gain is scored on a run, not on a claim, and the rubric states that written self-description
cannot substitute for runtime evidence. Measure it:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

It reports `coverage` (the share of your claims the supplied material supports) and `grounding` (the
share of your numbers that trace back to it), and with `--baseline` a skill-versus-baseline delta on the
same material. Exit 2 means the inputs were not comparable — fix the inputs, do not read it as a pass.
Put `gain.json` in the output directory: it is evidence the reviewer can re-run.


## Output requirements

Each case returns a structured result that keeps the input identifier, the main result, the
evidence/source locators, the run status and the uncertainty. Where a locator is available — page,
paragraph, table row and column, or figure caption — record it, and prefer the coarsest locator that
still lets a second person find the value unaided.

A field the material does not report is recorded as **not reported**, never as an empty value and never
guessed. The distinction between a value that is absent and a value that could not be extracted is part
of the deliverable, and both are reported honestly.
