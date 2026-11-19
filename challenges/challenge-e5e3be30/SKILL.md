---
name: claim-fact-verification
description: Use for 文献证据溯源与事实核验 — produce a verification table that judges each claim against the supplied sources from the supplied material, with every number, condition and citation traceable to a supplied source, a real editable artifact and an honest partial status.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan           # contract, check list, result.json skeleton
# ... read the case material and write the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md   # build, audit, conform, verify
```

`plan` takes no reading of its own and `finish` returns a JSON report whose `failed_checks` names
exactly what to repair. Everything else in this file explains what to put in the deliverable between
those two calls - the budget is for content, not for orchestration. `finish` exits non-zero if any
stage failed or a placeholder is still in `result.json`; repair and rerun it rather than shipping.

<!-- gain-evidence:begin -->
## Evidence you can reproduce (do this before you finish)

The comparison this channel scores under 使用增益 and 创新增益 is measurable, so measure it
instead of describing it. After the deliverable exists:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

It reports `coverage` (how many of your claims the supplied material supports) and
`grounding` (how many of your numbers trace back to it), and with `--baseline` a
skill-versus-baseline delta on the same material. Exit 2 means the inputs were not
comparable - fix the inputs, do not read it as a pass. Put the resulting `gain.json` in the
output directory: it is runtime evidence the reviewer can re-run, which prose cannot replace.
<!-- gain-evidence:end -->

## Budget order (do this first)

Three cases run three times each under a 64-request / 900-second budget, so the order matters more
than the length:

1. **Produce the deliverable file(s) now**, in the container format the case asks for, even if some
   sections are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json` with the original `case_id` and every original `output_contract` field**,
   with an honest `status` and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rebuild, verify, and update `result.json`.
   Never let step 3 run out the budget before step 1 has happened.

# 文献证据溯源与事实核验

Run this on the actual case now and deliver the artifact. Do not return a plan instead of the
deliverable, and do not invent a source, a measurement or a software state.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference (`material.json`,
  `environment/resources.yaml`, any workorder, the data, captions, statistics and literature).
  Read the actual content; a file name or a discipline label is not evidence.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Runtime: `"$SKILL_DIR/scripts/deliver.py"` (Markdown → genuine DOCX/PPTX/SVG, inspect, verify,
  optional PDF/PNG preview) and `"$SKILL_DIR/scripts/quantity_audit.py"` (declared number →
  declared source value). `SKILL_DIR` is the real directory of the loaded `SKILL.md`. Python
  3.10+, standard library only: no network, no pip, no doc-forge, no Office suite required.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Save an honest partial
  deliverable early, then improve it.
- A source that does not report a value is missing evidence, not evidence of absence. Write
  "not reported" and keep it out of the arithmetic. Never fabricate a DOI, a quotation, a
  statistic or a completed check.

## What this deliverable is

For each claim the case supplies, decide whether the sources support it, contradict it or cannot decide it, and show the exact passage relied on. Keep a compound claim split into its parts, do not let a literal quotation stand in for a semantic match, and record the reason for every verdict so another person can re-check it.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Inventory.** List every supplied file, what each one carries, and the locator of each fact
   you intend to use. Mark what is missing, illegible or contradictory.
2. **Ledger first.** Build the facts ledger (quantity, unit, condition, comparator, source
   locator, observation versus interpretation) before writing prose. Compute differences or
   percentages only from compatible units, with explicitly declared `ROUND_HALF_EVEN` rounding.
3. **Write the deliverable.** Use the genre the case names. Keep the case's own section titles
   and required filenames. Put the source pointer next to the claim it supports.
4. **Audit.** Write the quantity plan and run
   `python "$SKILL_DIR/scripts/quantity_audit.py" --plan /app/work/quantity-plan.json --outdir /app/work/quantity-audit`.
   It checks source versions, unique rows, finite values with units, exact unique quotes,
   declared numbers, compatible-unit arithmetic, adjacent units, coverage of every number in the
   section, and literal qualifiers. Exit 2 is a real mismatch: fix the text or the plan, never a
   hash.
5. **Build the artifact and verify it.**
   `python "$SKILL_DIR/scripts/deliver.py" build-docx --md <each markdown file> --out /app/output/deliverable.docx`
   then `verify` (real container format, text from the source, expected parts) and, if an Office
   renderer exists, `preview` — look at the PDF/PNG. If the renderer is absent, report that
   limitation instead of claiming a preview.
6. **Task-specific checks** — in addition to the audit, confirm and record:
- every claim has a verdict from supported / partially_supported / contradicted / insufficient_evidence
- each verdict quotes the passage it relies on with a locator
- compound claims are split and judged per part
- the verification is reproducible from the recorded locators alone

7. **Write `result.json`** with the original contract fields: deliverable paths, the preserved
   facts, the evidence map, the change log (what was written, what was narrowed, what awaits a
   human) and honest uncertainty. A partial result names exactly what is missing and why.
8. **Re-open your own output** before finishing: the audit status, each artifact and
   `result.json` must agree with each other.

## Failure handling

- Missing material: complete the supported part, name the missing file and locator, and keep the
  contract-compatible partial status. Do not silently drop a required section.
- Unreadable container (PDF/image): use only tools that are actually present, label uncertain
  readings, and never infer statistical meaning from appearance.
- Conflicting evidence: keep both sources, explain the disagreement, and ask the author.
- Format the case requires but the runtime cannot produce: keep the editable source, state the
  unmet constraint, and never rename a text file into the required extension.

## Numbers are checked automatically, not by hand

`finish` runs `scripts/number_scan.py` with no plan to write: it reads every number in your markdown,
reads every numeric value in the supplied data, and classifies each prose number as a declared value,
a declared two-value calculation, or undeclared. Undeclared numbers come back in the report's
`undeclared_numbers` list and make the run exit non-zero - that list is the traceability defect list
for the rubric's ?????? sub-point, so repair it before finishing. Add `--data <dir>` if the
supplied data is not under `/input`.

## Leave an evidence trail

The artifacts are all a reviewer sees, so a run that checked nine numbers and refused two claims
should not look like a run that did neither. Keep `work/run-evidence.json` as you go:

```json
{
  "sources_opened":   [{"path": "material/table-1.csv", "read": true, "note": "12 rows"}],
  "checks_run":       [{"id": "quantity:31.2MPa", "rule": "declared source value", "result": "pass"}],
  "claims_refused":   [{"claim": "...", "reason": "no source value; reported as not reported"}],
  "missing_material": [{"expected": "statistics table", "status": "absent", "handled": "narrowed"}],
  "limitations":      ["no Office renderer in this image; editable source kept"]
}
```

Copy it to the output directory as `run-evidence.json` and name it in `result.json` under
`deliverables` (or `evidence_map`, whichever the contract defines). An empty list means "none
encountered" and must be written explicitly; a missing file reads as "no checks were run".

## What the evaluation image provides

The organizer's own resource list for this challenge (`environment/resources.yaml`, declared per
channel in the published statement) names these as available in the pinned image:

- `execution-contract` - declared available for this challenge
- `scientific-python` - the Python stack for reading data, computing and writing files
- `scientific-tools-provenance` - declared available for this challenge
- `official-deepseek-harness` - the harness that runs this skill on the organizer's cases
- `pdf-text-tool` - extract the real text layer of a supplied PDF (never guess from a file name)
- `pdf-render-tool` - rasterise a PDF page when only the rendered page carries the information
- `ocr-tool` - read a scanned page or one whose text layer is broken
- `latex-compiler` - compile LaTeX when the case asks for it, and to check that it compiles
- `office-renderer` - render DOCX/PPTX to PDF (and pages to PNG) for the preview the runtime contract asks for
- `browser-automation` - open a supplied HTML/SVG artifact and check how it actually renders
- `font-discovery` - find which fonts exist before declaring a typographic constraint unmet

Two rules follow, and they cut both ways:

1. **Do not assume a tool is missing.** If the case asks for an editable artifact plus a rendered
   preview, produce both, using `office-renderer` (for Office formats) or `pdf-render-tool` /
   `browser-automation` (for PDF and SVG/HTML). A preview that exists is evidence; a sentence saying
   the renderer might not exist is not.
2. **Do not claim a tool that is not there.** Confirm availability by running it. If a declared tool
   genuinely fails in your image, keep the editable source, state which tool you tried and what it
   returned, and mark that specific part partial - never rename a text file into the required
   extension and never describe an output you did not produce.

## Worked micro-example (synthetic - the shape, not the content)

Question: "What yield did the treated group reach, and was the difference significant?"
Material: one paper with a results table and a discussion paragraph.

**Typical low-scoring answer**

> The treated group reached a yield of 82%, which is significantly higher than the control, showing
> that the treatment is effective. This is consistent with the literature.

Unsupported: the number may be right but there is no locator, "significantly" is invented, "is
effective" is a conclusion the paper may not draw, and "consistent with the literature" cites nothing.

**The same answer, compliant**

> **Answer.** The treated group reached 82% (Table 2, `paper/main.pdf` p.5; the text layer was read
> directly, not the rendered page). The control value is not reported in the supplied material, so the
> difference cannot be computed. The paper reports no significance test.
>
> **Evidence.** "the treated group reached a yield of 82%" - Table 2, row 4, quoted verbatim.
>
> **Refused.** "significantly higher" - the material contains no test statistic, p value or
> confidence interval. Recorded as not reported rather than inferred from error bars.
>
> **Confidence.** High for the 82% figure (verbatim table value). The absence of a control value is a
> material limitation, not a finding.

**The extraction table row that goes with it**

| item | value | unit | source | locator | status |
|---|---|---|---|---|---|
| treated yield | 82 | % | paper/main.pdf | Table 2 row 4 | extracted |
| control yield | - | - | - | - | not reported |
| significance | - | - | - | - | not reported |

A refusal is a deliverable: the -/not reported rows are what shows the question was read rather than
partially guessed.

## Materials in this submission

| Path | What it answers |
|---|---|
| `RUBRIC.md` | this channel's published sub-points, each mapped to the artifact that covers it |
| `GAIN.md` | how the platform's baseline-versus-skill comparison is answered, and how to reproduce the fixture measurements |
| `INNOVATION.md` | the capability the base agent lacks, the method change, the boundary and the evidence |
| `ECOSYSTEM.md` | documentation completeness and the reusable resources, generated from the real file list |
| `CHECKLIST.md` | one pass-through list per run, one question per published sub-point |
| `CHANGELOG.md` | versioning and maintenance policy |
| `templates/` | glossary, reference map, change log, deliverable plan and pointer templates |
| `tests/cases/` | reusable interface items with structural expectations |

These are submission materials, not case answers: no organizer case, whiteboard or formal result is
included anywhere in this bundle.

## Minimal example (synthetic, not a case)

```
python "$SKILL_DIR/scripts/quantity_audit.py" --plan /app/work/fixture/plan.json --outdir /app/work/audit
python "$SKILL_DIR/scripts/deliver.py" build-docx --md results.md --md discussion.md --out /app/output/deliverable.docx
python "$SKILL_DIR/scripts/deliver.py" verify --out-file /app/output/deliverable.docx --md results.md --outdir /app/work/check
```

The fixture ships in `examples/synthetic_case.py`; its numbers are interface-test values, not
case results and not a score.
