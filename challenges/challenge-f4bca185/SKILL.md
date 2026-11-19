---
name: contract-driven-reading-answers
description: Use when supplied material must be read into a checkable answer — one result per requested field or question, every reported value carrying a locator and a verbatim quotation, unreported and conflicting items stated as such, and a contract check that catches a guessed value.
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

# Contract-driven reading answers

Run this on the actual case and deliver the answer. Do not fill a field the material does not carry,
do not quote a sentence you did not read, and do not let a partial reading look complete.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the abstract,
  body paragraphs, table text, figure captions, reference metadata, any field list or question list,
  `environment/resources.yaml`. Read the actual text; a section title is not the passage.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Tool: `"$SKILL_DIR/scripts/reading_contract.py"` (`SKILL_DIR` = the real directory of the loaded
  `SKILL.md`). Python 3.10+, standard library only: no network, no pip, no PDF or OCR library.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- The answer is checked line by line: every requested item appears once, every `reported` value has
  a locator and a quotation that is actually in the material, and every gap is stated in the case's
  own status vocabulary.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Extract the contract.**
   `python "$SKILL_DIR/scripts/reading_contract.py" contract --case /input/case.json --out /app/work/contract.json`
   (add `--fields`/`--questions` when they are separate files). It lists every requested field id
   and question id with the status vocabulary the case uses, so nothing can be silently dropped.
2. **Read the material and fill the entries.** For each requested field: the value exactly as the
   material states it (with its unit), the paragraph/section/page locator, and a short **verbatim**
   quotation. For each question: the answer, its conditions, its claims with evidence entries, and
   the parts you could not answer. Use the case's vocabulary:
   - fields: `reported` / `not_reported` / `source_conflict` / `extraction_failed`
   - questions: `answered` / `partial` / `insufficient_evidence` / `input_error`
   A value the material does not report is `not_reported` **with no value**; if two passages
   disagree it is `source_conflict` and both locators are named.
3. **Check the answer.**
   `... check --answer /app/work/answer.json --case /input/case.json --outdir /app/work/check`
   It proves: every requested id answered once, statuses on-vocabulary, no value attached to a
   `not_reported` field, every `reported` field carrying locator + quotation, every quotation
   verbatim in the supplied text, conflicts naming two locators, every value's digits present in its
   own quotation, and claims carrying evidence. Exit 3 lists the failing checks by id.
4. **Verify the envelope.** `... verify --answer /app/work/answer.json --outdir /app/work/check`
   proves the answer keeps its `case_id`, carries a status from the case vocabulary and contains
   every field the case's own contract requires.
5. **Write `result.json`** with the original contract fields plus the reading result: the field
   results with their evidence, the question answers, the claims, and the uncertainties — an
   uninspected range, an ambiguous passage, a field whose unit the material never states.
6. **Re-open your own output** before finishing: the check status is `verified`, every quotation in
   the answer appears in the material, and no `not_reported` field carries a number.

## Failure handling

- Material that cannot be read (an image you cannot decode, a truncated file): report
  `extraction_failed` for the affected fields, name the file, and keep the rest of the answer — never
  infer the value from the surrounding text.
- A passage that could support two readings: give the reading you chose, quote the passage, and list
  the alternative in the uncertainties. Do not silently pick the convenient one.
- A question that needs a comparison the material does not make: answer `partial` and list the gap.
- Never quote from memory: if you cannot copy the sentence from the supplied text, you have not read
  it, so the field is `not_reported` or `extraction_failed`.

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
python "$SKILL_DIR/scripts/reading_contract.py" contract --case /app/work/fixture/case.json --out /app/work/contract.json
python "$SKILL_DIR/scripts/reading_contract.py" check --answer /app/work/fixture/answer-good.json --case /app/work/fixture/case.json --outdir /app/work/check
python "$SKILL_DIR/scripts/reading_contract.py" verify --answer /app/work/fixture/answer-good.json --outdir /app/work/check
```

Illustrative behaviour on that fixture: the contract lists 5 fields and 2 questions, the compliant
answer passes 11/11 checks, and the deliberately defective answer fails field coverage, the status
vocabulary, the value-on-unreported rule, the locator rule, quotation fidelity, numeric preservation
and claim evidence. Those values come from `examples/synthetic_case.py` — an interface fixture, not a
case result and not a score. See `MAPPING.md`.
