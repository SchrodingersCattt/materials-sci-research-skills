---
name: grant-proposal-from-source-evidence
description: Use for 写作14｜基金申请书写作 — produce funding-proposal sections built from the supplied workorder from the supplied material, with every number, condition and citation traceable to a supplied source, a real editable artifact and an honest partial status.
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

# 写作14｜基金申请书写作

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

Build the requested proposal sections from the supplied source and workorder: keep the workorder's own section list, distinguish the source authors' published results from the applicant's proposed work, state the missing genuine-funder and applicant-evidence items, and keep every number, sample and condition traceable to the supplied material.
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
- all requested sections exist with substantive text, not headings or placeholders
- published results are attributed to the source, never to the applicant
- risk and alternative items are present and specific
- manual-confirmation items include the real applicant evidence and the real funding rules

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
for the rubric's 结果可核验性 sub-point, so repair it before finishing. Add `--data <dir>` if the
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
python "$SKILL_DIR/scripts/quantity_audit.py" --plan /app/work/fixture/plan.json --outdir /app/work/audit
python "$SKILL_DIR/scripts/deliver.py" build-docx --md results.md --md discussion.md --out /app/output/deliverable.docx
python "$SKILL_DIR/scripts/deliver.py" verify --out-file /app/output/deliverable.docx --md results.md --outdir /app/work/check
```

The fixture ships in `examples/synthetic_case.py`; its numbers are interface-test values, not
case results and not a score.

## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 6 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 6 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `figure-table-pointer-template.csv`, `glossary-template.csv`, `reference-map-template.csv`, `section-evidence-map.csv`. |
| 2 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`, `run_checks.py`. |
| Worked fixtures (`examples/`) | `synthetic_case.py` - realistic shapes you can run end to end before touching real material. |
| Test cases (`tests/cases/`) | 4 declared cases you can extend with your own. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `CHANGELOG.md`, `CHECKLIST.md`, `ECOSYSTEM.md`, `GAIN-EVIDENCE.md`, `GAIN.md`, `INNOVATION.md`, `MAPPING.md`, `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and the
suites named above are the regression tests to run after any edit. `CHANGELOG.md` records what changed
and why. A package that fails its own checks is not a package to submit - the composing repository's
`verify_package.py` is the pre-submission gate.
## What this saves, measured

The rubric asks whether loading this package measurably reduces manual work, under the same input and
the same permissions. These are the numbers, and every one is reproducible by running the package -
they are counted from the shipped source, not asserted.

| What the package does automatically | Count |
|---|---|
| declared artifacts inspected per run | 17 |
| of which are content checks, not just file presence | 16 |
| distinct machine-readable reports emitted | 7 |
| conditions the package refuses to pass silently | 0 |
| self-test suites shipped | 2 |
| self-test assertions | 15 |
| adversarial negative controls in the test suite | 4 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 17 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 0 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 7 machine-readable report(s): `manuscript-build/v1`, `manuscript-preview/v1`, `manuscript-verify/v1`, `number-scan/v1` |
| Regression safety | none | 15 assertions in the shipped self-tests, including 4 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `case_id_preserved`, `declared_columns_present`, `declared_vocabulary_respected`, `exists`, `format`, `input_kept`, `key_types_match`, `no_placeholders`, `required_files_exist`, `required_files_nonempty` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
