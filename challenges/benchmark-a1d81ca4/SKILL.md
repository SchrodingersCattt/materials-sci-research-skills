---
name: benchmark-case-authoring
description: Use when a literature-reading or academic-writing benchmark must be built, reviewed or scored — author cases with resolvable material and explicit scoring anchors, validate the set mechanically, then score answers reproducibly with the declared rule instead of an impression.
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

# Benchmark case authoring

Run this on the actual case and deliver the benchmark artefact it asks for. Do not present a case
set whose expected answers you cannot point at, and do not report a score you cannot recompute.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the topic, the
  supplied sources, any workorder, `environment/resources.yaml`. Read the actual material; a title
  is not a source.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Tool: `"$SKILL_DIR/scripts/benchmark_build.py"` (`SKILL_DIR` = the real directory of the loaded
  `SKILL.md`). Python 3.10+, standard library only: no network, no LLM call, no grading service.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- A benchmark you author must be **runnable by someone else**: every case carries its material
  locator, its expected-answer contract and its scoring anchors, and the score is computed by a
  declared rule rather than by an impression.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Decide the case set from the task.** For each case: the instruction, the material it rests on
   (file + locator), the expected-answer contract (fields, values, conditions that must be
   preserved) and the scoring anchors. Cases should differ in what they test — a reading case that
   checks reported values, a writing case that checks whether an association was overstated — not
   in superficial wording.
2. **Write the spec.** One JSON file: `{"title", "purpose", "min_cases", "scoring_rule",
   "cases": [{"id", "kind", "title", "instruction", "material": [{"path", "locator"}],
   "expected": {...}, "max_points", "anchors": [{"id", "kind": "required|bonus|penalty",
   "points", "text", "match_any": [...]}]}]}`. The earnable anchors (required + bonus) must sum to
   `max_points`; penalties are separate and subtract.
3. **Validate.**
   `python "$SKILL_DIR/scripts/benchmark_build.py" validate --spec /app/work/benchmark.json --outdir /app/work/benchmark`
   Checks required fields, unique ids, anchor kinds and weights, that earnable weights equal the
   declared maximum, that every material path resolves, and that each case declares a non-empty
   expected-answer contract. Exit 2 means the set is not runnable yet — fix it, do not ship it.
4. **Score with the declared rule.**
   `... score --spec ... --answers /app/work/answers.json --outdir /app/work/scoring`
   Every anchor is matched against the answer, required anchors that miss are listed by id, matched
   penalties are subtracted and the total is clipped to the maximum. The report records the spec
   hash and the answer hash, so the same inputs produce the same score.
5. **Verify and report.** `... verify --spec ... --outdir ...` re-validates and confirms the rule
   is computable from the set alone. Then write the deliverable: the case set, the validation
   report, the scoring report, the anchors with the evidence each one rests on, and the exact
   command to reproduce the score.
6. **Write `result.json`** with the original contract fields: the artifact paths, the preserved
   facts, the anchor→evidence map, the change log and honest uncertainty — a case whose material
   could not be resolved, an anchor that is ambiguous, a scoring rule the case did not specify.
7. **Re-open your own output** before finishing: the validation status is `valid`, every declared
   material path exists, and no anchor claims evidence the material does not contain.

## Failure handling

- Material that cannot be resolved: the validator reports the path; either fix the path or remove
  the case and say so. Never score a case whose source is missing.
- A scoring rule the case leaves open: choose the simplest computable one, declare it in the
  report, and record that the case did not specify it.
- An anchor that could be matched by an unrelated phrase: tighten `match_any` or move it to
  `penalty`; note every ambiguity you could not remove.
- Never present this score as an official platform score, and never invent a model-judged score.

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
python "$SKILL_DIR/scripts/benchmark_build.py" validate --spec /app/work/fixture/benchmark-spec.json --outdir /app/work/benchmark
python "$SKILL_DIR/scripts/benchmark_build.py" score --spec /app/work/fixture/benchmark-spec.json --answers /app/work/fixture/answers-reference.json --outdir /app/work/scoring
python "$SKILL_DIR/scripts/benchmark_build.py" verify --spec /app/work/fixture/benchmark-spec.json --outdir /app/work/benchmark
```

Illustrative behaviour on that fixture: the set validates, the reference answers reach
`normalised_total = 1.0`, and a weak answer set that overstates significance is scored strictly
lower with both penalties matched. Those values come from `examples/synthetic_case.py` — an
interface fixture, not a case result and not a platform score. See `MAPPING.md`.
