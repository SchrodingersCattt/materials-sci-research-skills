---
name: methods-and-experimental-sections
description: Use when methods and experimental sections must be written for reproducibility: ordered steps, parameters, datasets, controls, and explicit limitations.
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


# 方法与实验章节写作 — write methods that can be reproduced

## Engine

`scripts/evidence_ledger.py` — bind every sentence in the deliverable to a supplied source, so a
statement with no source cannot reach the output unnoticed.

```bash
python "$SKILL_DIR/scripts/evidence_ledger.py" extract --doc /input/material --sources /input     --out work/ledger.json
# ... write work/draft.md, citing ledger entries ...
python "$SKILL_DIR/scripts/evidence_ledger.py" audit --ledger work/ledger.json --out work/audit.json
python "$SKILL_DIR/scripts/evidence_ledger.py" verify --ledger work/ledger.json --sources /input     --out work/verify.json
python "$SKILL_DIR/scripts/evidence_ledger.py" report --ledger work/ledger.json --out /app/output/change-log.csv
```

1. **`extract`** builds the ledger: one record per claim found in the supplied document, each with its
   source locator, the conditions attached to it, and its strength (reported / hedged / not reported).
   `--citation-map` takes an explicit citation-to-source mapping when the material provides one.
2. **`audit`** reports the defects that matter for this channel: a sentence in the draft with no ledger
   record, a record never used, a number that disagrees with its source, and a hedge that was promoted
   to a statement of fact.
3. **`verify`** re-checks the ledger against the sources, so a record cannot cite something that is not
   there.
4. **`report`** emits the modification record the rubric asks for.


## What this must get right

- **Every factual sentence traces to a fact record.** The audit reports untraced sentences, and the
  deliverable is not finished while any remain.
- **Numbers, units and conditions travel together.** A value stated without its condition is a defect,
  because the rubric scores exactly that.
- **Hedging is preserved.** A source that says `may`, `提示` or `suggested` does not become a statement of
  fact in the output, and the audit flags any promotion.
- **Absences are stated as absences.** Where the material does not report something, the deliverable
  says so rather than writing around it.
- **Steps are ordered and complete.** A step that cannot be performed from the text is a defect, and
  the audit reports missing parameters by name.
- **Parameters carry units and conditions.** A number without a unit or without its condition is
  reported.
- **Controls and comparisons are stated explicitly**, including their purpose.
- **Limitations are stated, not omitted.** The rubric scores whether constraints are named; the ledger
  keeps them as facts so they cannot be quietly dropped during assembly.


## What it must refuse

- **Refuse to write a sentence with no source.** If the material does not support it, it does not go in.
- **Refuse to invent a citation, a number, or a condition.** A missing reference is reported as missing.
- **Refuse to smooth over a conflict.** Two sources that disagree are reported as a conflict for a human
  to resolve, not averaged or silently chosen between.
- **Refuse to present a draft as finished** when the audit still reports untraced sentences.
- **Refuse to supply a plausible parameter** the material does not report. Report it as not reported.
- **Refuse to describe a procedure the material does not describe**, even if the outcome is known.


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
