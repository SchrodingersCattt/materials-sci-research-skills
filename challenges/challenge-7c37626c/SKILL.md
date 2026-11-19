---
name: exact-formula-derivation
description: Use for formula parsing and mathematical reasoning — read the expression and its variables from the supplied material, evaluate exactly with declared assumptions and domains, state ranges only where the material states them, and deliver a re-runnable step ledger instead of an approximate number.
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

# Exact formula derivation

Run this on the actual case and deliver the derived quantities. Do not present an approximate
number as the checked value, do not fill a variable the material does not report, and do not
attach a range the material never states.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the formula or
  derivation as given, the variable values, the units, the stated bounds, `environment/
  resources.yaml`. Read the actual symbols; a label or a familiar-looking equation is not
  evidence that its variables mean what you expect.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Tool: `"$SKILL_DIR/scripts/formula_check.py"` (`SKILL_DIR` = the real directory of the loaded
  `SKILL.md`). Python 3.10+, standard library only: no network, no pip, no sympy.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Arithmetic is **exact**: rationals as fractions, decimals as their exact decimal value.
  Floating point is not the checked value; if a computation would need it, the step is reported
  instead of approximated.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Transcribe before computing.** Write down the expression exactly as the material gives it,
   and for every symbol: its meaning, its declared value, its unit, its source locator, and any
   domain or bound the material states. A symbol with no reported value stays unassigned.
2. **Write the spec.** One entry per derivation step:
   `{"id": "...", "expression": "...", "source_locator": "...", "variables": {"m1": {"value":
   "2", "source_locator": "table row 1"}}, "domains": {"m1": "> 0"}, "unit": "m/s",
   "declared_range": {"lower": "...", "upper": "...", "source_locator": "..."},
   "display_places": 4}`. Only `+ - * / ^` and `abs/min/max` are supported — an expression that
   needs more must be rewritten into that form and the rewrite recorded.
3. **Check.**
   `python "$SKILL_DIR/scripts/formula_check.py" check --spec /app/work/formula.json --outdir /app/work/formula`
   Each step gets a status: `ok`, `mismatch`, `domain_violation`, `unresolved_denominator` or
   `error`, plus the readable substitution, the exact value (`numerator/denominator`), the
   display rounding, the unit, and a note saying whether a range came from the material or the
   material states none. Exit 2 means a real problem in the derivation or in the declared values.
4. **Verify and write up.**
   `... verify --spec /app/work/formula.json --outdir /app/work/formula` proves the arithmetic
   is reproducible and every step carries its range note; then put the step table into the
   deliverable with: the expression, the substitution, the exact value, the unit, the stated
   range (or "the material states no range"), the assumptions, and every unresolved item.
5. **Write `result.json`** with the original contract fields: the deliverable path, the preserved
   facts, the symbol→source map, the change log (any algebraic rewrite and why), the exact
   results, and honest uncertainty — a symbol with no reported value, a bound the material never
   states, a unit the material does not define.
6. **Re-open your own output** before finishing: every number in `result.json` appears in the
   formula report with the same exact value, and no step claims a range the spec does not declare.

## Failure handling

- A variable the material does not report: leave it unassigned and report the step as an error
  naming the symbol — never substitute a plausible value.
- A denominator that can be zero under the declared values: report `unresolved_denominator` and
  state which variables make it zero. Only evaluate after the material (or the agent, explicitly
  and with a locator) declares the denominator non-zero.
- An expression outside the supported operators: rewrite it, record the rewrite in the change
  log, and re-check; do not silently approximate.
- A unit the material does not define, or a unit conversion it does not state: carry the unit
  verbatim and record the gap. No unit algebra is performed.

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

Material: `material/table-1.csv` with `A,31.2,MPa` and `B,24.0,MPa`, plus `material/stats-note.md`
which states that no significance test was run.

**Typical low-scoring paragraph**

> Both specimens showed strong mechanical performance. Specimen A reached 31.2 MPa, significantly
> higher than B at 24.0 MPa, demonstrating that the treatment improves strength by 30%.

Three defects, each of which the audit and the rubric both punish: "significantly" reports a test the
material does not contain; "by 30%" is an undeclared calculation (and the base is unstated); and
"demonstrating that the treatment improves" turns a two-specimen comparison into a causal claim.

**The same content, compliant**

> Specimen A reached 31.2 MPa and specimen B reached 24.0 MPa (Table 1; `material/table-1.csv`, rows
> A and B). The difference is 7.2 MPa in favour of A, computed from the two declared values in
> compatible units and rounded to one decimal place. Because the material reports no significance
> test, no difference is claimed here in statistical terms.

Every number in the second version is either a declared source value (31.2, 24.0), a declared
compatible-unit calculation (7.2, declared rounding), or absent. The limitation is stated in the same
sentence as the comparison rather than buried later.

**Its evidence map rows**

| claim_id | claim_quote | source_file | locator | strength |
|---|---|---|---|---|
| C-001 | "Specimen A reached 31.2 MPa" | material/table-1.csv | row A, value column | supported |
| C-002 | "The difference is 7.2 MPa" | derived | 31.2 - 24.0, compatible units | supported (declared calculation) |
| C-003 | "the material reports no significance test" | material/stats-note.md | full document | supported (documented absence) |

**The discussion sentence that pairs with it** (one finding, one supplied source, verdict stated):

> The direction of the difference agrees with the supplied literature (`literature/ref-1.md`, §3),
> which reports the same ordering at a different load. That source does not supply a mechanism, so no
> mechanism is proposed here.

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
python "$SKILL_DIR/scripts/formula_check.py" check --spec /app/work/fixture/formula-spec.json --outdir /app/work/formula
python "$SKILL_DIR/scripts/formula_check.py" verify --spec /app/work/fixture/formula-spec.json --outdir /app/work/formula
```

Illustrative behaviour on that fixture: the rational step reports `exact = 11/6` with a
`1.8333` display, the volume step carries the range the fixture states, the rate step with a
zero denominator is reported as `unresolved_denominator`, and the pressure step is an `error`
because the fixture never reports the temperature. Those values come from
`examples/synthetic_case.py` — an interface fixture, not a case result and not a score.
See `MAPPING.md`.
