---
name: literature-review-generation
description: Use when a literature review must be generated from supplied sources: screening criteria written before writing, themes derived from the sources, an evidence table, and a draft whose strength words match the evidence.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan
# ... read the case material and produce the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md
```

`plan` takes no reading of its own. `finish` returns a JSON report whose `failed_checks` names exactly
what to repair, and exits non-zero if a stage failed or a placeholder is still in `result.json`.

## Budget order (do this first)

1. **Produce the deliverable now**, in the container format the case asks for, even if some findings
   are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rebuild, verify, update `result.json`.


## Contract

- Read the real `/input/case.json` and `task.md` and every material they reference, including
  `environment/resources.yaml`. Read the actual files; a filename is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only. No network. Declared tools include `pdf-text-tool`, `pdf-render-tool`,
  `ocr-tool`, `latex-compiler`, `office-renderer`, `scientific-python`.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# 文献综述生成 — screening, themes, evidence table, draft

## Engine

`scripts/evidence_ledger.py` plus `scripts/chapter_consistency.py`.

```bash
python "$SKILL_DIR/scripts/evidence_ledger.py" extract --doc /input/material/notes.md \
    --sources /input/material --out work/ledger.json
python "$SKILL_DIR/scripts/evidence_ledger.py" audit --ledger work/ledger.json --out work/audit.json
python "$SKILL_DIR/scripts/chapter_consistency.py" audit --chapters work/draft/*.md \
    --references work/ledger.json --out work/consistency.json
```

The ledger is the evidence table: one record per claim with its source, conditions and strength. The
consistency audit then proves that the draft's themes agree with each other and that every citation
resolves.


## What this must get right

- **A finding is a hypothesis with a locator, never a verdict.** Each one names the span it came from,
  so a reviewer can accept, partly accept or reject it.
- **Findings are real.** Do not report a defect that is not there; a false positive costs more than a
  miss, because it teaches the reviewer to distrust the list.
- **Severity is discriminating.** If everything is "medium" the list is useless. Rank by what would
  change a reader's conclusion, not by how easy the item was to spot.
- **Suggestions are executable.** Name what to add, which sentence to narrow, which claim to soften.
  "Strengthen the argument" is not a suggestion.
- **Long documents are fully covered.** If the text was truncated or a section could not be parsed,
  say which span was not reviewed. Never present a partial pass as a complete one.
- **Inclusion and exclusion criteria are written before the draft**, and applied consistently; the
  screening record lists every source with its decision and reason.
- **Themes come from the sources, not from a template.** Each theme names the sources that support it
  and states its boundary.
- **Draft strength words match the evidence**: "established", "suggestive" and "contested" are used
  according to what the evidence table says, not for rhetorical variety.
- **Conflicting evidence is presented side by side**, and the research gap is placed at a specific gap
  in the evidence, not asserted in a closing sentence.


## What it must refuse

- **Refuse to report a defect without a locator.** If it cannot be pointed at, it is not a finding.
- **Refuse to treat a deliberate choice as an error.** A control group, a stated assumption, or a
  quotation of another author's view is not a self-contradiction.
- **Refuse to claim full coverage** when a section failed to parse, a figure could not be read, or the
  document was truncated.
- **Refuse to invent a citation or a reference.** A missing entry is reported as missing.


## Evidence you can reproduce

Use gain is scored on a run, not a claim, and the rubric states that written self-description cannot
substitute for runtime evidence:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

`coverage` is the share of your findings the supplied material supports; `grounding` is the share of
your numbers that trace back to it. Exit 2 means the inputs were not comparable. Ship `gain.json`.


## Output requirements

Each case returns a structured result that keeps the input identifier, the main result, the
evidence/source locators, the run status and the uncertainty. Every finding carries: the dimension it
belongs to, the locator, the evidence quote, a severity, and an executable suggested action. Where a
judgement is subjective, state the reference standard you applied, the acceptable range and what
remains uncertain. A span that was not reviewed is reported as not reviewed.
