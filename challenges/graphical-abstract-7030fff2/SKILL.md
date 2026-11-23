---
name: graphical-abstract-figure
description: Use for Graphical Abstract（图形摘要） — deliver a single-page graphical abstract from the supplied material, with every element traceable to a source locator, a real editable SVG source plus PNG and PDF exports, and a source-preserving edit record when the case supplies a figure or template.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan          # contract, check list, result.json skeleton
# ... read the material, decide what the figure must show, build it ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md   # build, audit, conform, verify
```

`plan` takes no reading of its own; it states the contract the case asks for and the checks that will be
applied. `finish` returns a JSON report whose `failed_checks` names exactly what to repair, and exits
non-zero if a stage failed or a placeholder is still in `result.json`.

## Budget order (do this first)

Three cases run three times each under a 64-request / 900-second budget, so the order matters more than
the length:

1. **Produce the deliverable file(s) now**, in the format the case asks for, even if some panels or
   values are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, with an
   honest `status` and the uncertainties already known.
3. **Then iterate**: inspect the render, repair what the check names, rebuild, verify, update
   `result.json`. Never let step 3 run out the budget before step 1 has happened.


## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the source document,
  the data behind any chart, the supplied figure or template, the workorder, and
  `environment/resources.yaml`. Read the actual files; a label is not evidence.
- Work in `/app/work`; deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting and
  types, and an honest `status`.
- Tools: `"$SKILL_DIR/scripts/make_figure.py"` (chart/diagram build, inspect, verify) and
  `"$SKILL_DIR/scripts/edit_svg.py"` (source-preserving edit of a supplied SVG). `SKILL_DIR` is the real
  directory the loaded `SKILL.md` lives in; if it is not already exported, resolve it once from the
  `SKILL.md` path you were given and export it (`export SKILL_DIR=...`, then
  `python "$SKILL_DIR/scripts/make_figure.py" chart --help`) — every command in this file depends on it.
- Python 3.10+, **standard library only**: no network, no pip, no plotting package, no python-pptx. A
  LibreOffice renderer, if present, only adds a preview.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.


# a single-page graphical abstract: question, method, core result and conclusion

## Engine

`scripts/make_figure.py` — the figure build, made mechanical.

```bash
python "$SKILL_DIR/scripts/make_figure.py" chart       --spec work/figure.json  --out-prefix /app/output/figure1
python "$SKILL_DIR/scripts/make_figure.py" diagram     --spec work/diagram.json --out-prefix /app/output/figure1
python "$SKILL_DIR/scripts/make_figure.py" inspect-png /app/output/figure1.png
python "$SKILL_DIR/scripts/make_figure.py" verify      --prefix /app/output/figure1 --spec work/figure.json \
    --outdir /app/work/check
```

Each build writes five files into `/app/output`: the editable `.svg`, the `.png` raster export, the
`.pdf` print export, the layered `.drawio` source (every element addressable by id), and a
`.provenance.csv` mapping element id → source file and locator. The editable source is itself one of the
scored elements, so delivering only the PNG fails it.

`scripts/edit_svg.py` — the source-preserving edit of a figure the case supplies.

```bash
python "$SKILL_DIR/scripts/edit_svg.py" --source /input/figure.svg --plan work/edit-plan.json \
    --outdir /app/output/edited
```

`work/edit-plan.json` names `source_sha256` (so a different input is refused as stale) and `edits`, each
`{"id": "<element id>", "kind": "text" | "fill", "old": "<value in the source>", "new": "<value to write>",
"workorder_id": "<the requested change>", "reason": "<why>"}`. Every edit must match the source exactly;
the tool refuses an ambiguous target, an unrequested change and a source whose structure changed, then
writes `edited.svg` plus `svg-edit-report.json` recording the before/after hashes. Use it whenever the
case supplies a figure or template to modify; do not redraw a supplied figure from scratch and do not
claim an edit the record does not show.


`scripts/route_svg.py` — a normalized box-and-arrow route from an explicitly authored plan.

```bash
python "$SKILL_DIR/scripts/route_svg.py" --plan work/route.json --outdir /app/output/route
```

It requires a source and locator on every node and edge, explicit node ids, non-overlapping bounded
geometry and supported flow types, and it cannot infer scientific correctness, render an apparatus, or
certify readability. Use it for an explicit orthogonal route; for anything else, use `make_figure.py` or
state the limitation.


## Minimal call example (interface example, not a case answer)

`examples/` holds one chart spec, one diagram spec and the tiny CSV the chart reads. They show the
interface only; their numbers are interface-test values and are **not** case results. Run them once
before touching the real material so a wrong invocation is not discovered at the end of the budget:

```bash
python "$SKILL_DIR/scripts/make_figure.py" chart   --spec examples/chart-spec.json   --out-prefix /app/work/smoke
python "$SKILL_DIR/scripts/make_figure.py" diagram --spec examples/diagram-spec.json --out-prefix /app/work/smoke
python "$SKILL_DIR/scripts/make_figure.py" verify  --prefix /app/work/smoke --spec examples/diagram-spec.json \
    --outdir /app/work/smoke-check
```

Spec fields actually read by the builder — a chart spec takes `kind` (`bar`/`line`/`scatter`), `data`
(a CSV path), the column names in `x` / `value` / optional `series` / `error_low` / `error_high`, plus
`unit`, `title`, `x_label`, `y_label`, `note`, `source`, `error_meaning`, `width`, `height`. A diagram
spec takes `nodes` (`id`, `label`, optional `detail`, `position`, `x`, `y`, `w`, `h`, and the `source` /
`locator` pair that ties the element to the material), `edges` (`from`, `to`, optional `label`), plus
`legend`, `title`, `caption`, `default_position`, `width`, `height`. Geometry is in the same pixel space
as `width`/`height`, so keep every node inside the canvas.


## What this must get right

- **Every element, relationship and number names where it came from.** A box, an arrow, a label or a
  value with no source locator is the failure this track names first.
- **The four elements are covered**: the question, the method, the core result and the conclusion, each
  visibly present, plus the legend, units, scale and condition labels the figure needs to be read.
- **A code and legend that match the data.** Whatever the chart encodes must be the value in the
  material, with the unit, and the legend must say which channel encodes what.
- **The space is honest.** Spatial or causal ordering must follow the material: no arrow that reverses
  the reported direction and no hierarchy the material does not state.
- **A supplied artifact is edited, not replaced.** Change only the requested elements, keep everything
  else byte-identical, and list what changed.
- **The export is checked, not promised.** Report the canvas size, the export formats, and whether the
  raster inspection found clipping, overflow or a blank region — and fix them rather than shrinking text
  until the warning stops.

## What it must refuse

- **Refuse to draw a value, a unit, a legend entry or a conclusion the material does not support.** Say
  what the material would need to contain instead.
- **Refuse to present a mechanism or a causal direction the material does not establish**; mark it as a
  hypothesis in the caption or leave it out.
- **Refuse to deliver a flattened bitmap as the editable source.** An export alone is not the source.
- **Refuse to claim an edit that the record does not show**, and never silently rewrite an untouched
  element of a supplied figure.
- **Refuse to assert a preview or a font that was not actually produced**; a missing renderer is a stated
  limitation in `result.json`.


## Evidence you can reproduce

Use gain is scored on a run, not a claim:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

`coverage` is the share of your claims the supplied material supports and `grounding` the share of your
numbers that trace back to it. Exit 2 means the inputs were not comparable — fix them, do not read it as
a pass. Ship `gain.json`: it is runtime evidence a reviewer can re-run.

## Output requirements

Each case returns a structured result holding the input identifier, the artifact paths, the
element→source map, the export and edit checks, the run status and the uncertainty. An element the
material cannot support is reported as unsupported rather than drawn, and the run states which part of the
material it did not cover.

## Minimal call example (synthetic - interface only, not an answer)

Row 4 of the organizer's delivery table asks for at least one set of inputs, the invocation, and a
sample output marked as an example. Everything below is **synthetic**: the case id is
`SYNTHETIC-EXAMPLE-0001`, the material invents two rows and deliberately leaves one value
absent, and the transcript under it is the **real captured output** of running these commands in this
package. It demonstrates the interface; it is not an answer to any case, and it is not a score.

### The inputs (`examples/`)

| File | What it is |
|---|---|
| `examples/case.json` | a synthetic case; its output contract declares `confidence`, `evidence_map`, `key_findings`, `limitations`, `summary`, plus the deliverable `findings.csv` |
| `examples/task.md` | the synthetic task text |
| `examples/material/synthetic-material.md` | invented material whose catalyst loading is genuinely absent |

### The invocation

```bash
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpr34iezch/example/work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpr34iezch/example/work/contract.json --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpr34iezch/example/work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpr34iezch/example/work
# ... read examples/material/, write the deliverable and work/result.json ...
```

### Sample output (real transcript from these commands)

Paths in the transcript are written `<WORKDIR>` because they differ on every machine; everything else
is exactly what the commands printed.

| Command | Exit | Output |
|---|---|---|
| `contract_check.py extract` | 0 | `{"keys": 5, "files": 0, "columns": 0, "checklist": 7}` |
| `contract_check.py skeleton` | 0 | `{"keys": ["case_id", "confidence", "evidence_map", "key_findings", "limitations", "summary"]}` |
| `run_case.py plan` | 0 | `{"case_found": true, "contract_names": {"keys": ["summary", "key_findings", "evidence_map", "limitations", "confidence"], "files": [], "columns": []}, "stages": {"contract": 0}}` |

Each command below is one this package actually ships; the transcript under it was produced by running exactly these lines against `examples/`.
`extract` reports how many contract keys, files and columns it found; `skeleton` lists the keys the
result must carry, including `case_id`; `plan` writes the checklist and names what to do next. On a real
case the same commands run against `/input/case.json` and `/input/task.md` unchanged - only the paths
differ, which is exactly why the example is included: it proves the interface works end to end.

The synthetic material's absent catalyst loading exists so the example shows the honest path: the
deliverable must say "not reported", and the audit fails the run if a number appears that the material
never stated.
## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 7 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 3 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `reference-map-template.csv`. |
| 6 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `analysis_checks.py`, `file_inventory_checks.py`, `gain_checks.py`, `protocol_audit_checks.py`, `retrieval_checks.py` and more. |
| Worked fixtures (`examples/`) | `chart-data.csv`, `chart-spec.json`, `diagram-spec.json` - realistic shapes you can run end to end before touching real material. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Optional: a LibreOffice/PDF renderer. If one is present the build also emits a raster preview and says so; if not, the exports still exist and the report names the missing preview as an explicit limitation rather than inventing one.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `PROVENANCE.md`.

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
| declared artifacts inspected per run | 19 |
| of which are content checks, not just file presence | 15 |
| distinct machine-readable reports emitted | 7 |
| conditions the package refuses to pass silently | 6 |
| self-test suites shipped | 6 |
| self-test assertions | 118 |
| adversarial negative controls in the test suite | 16 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 19 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 6 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 7 machine-readable report(s): `figure-build/v1`, `figure-verify/v1`, `number-scan/v1`, `output-contract-check/v1` |
| Regression safety | none | 118 assertions in the shipped self-tests, including 16 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `artifact{suffix`, `case_id_preserved`, `check_layout`, `declared_columns_present`, `declared_labels_present`, `declared_values_drawn`, `declared_vocabulary_respected`, `format{suffix`, `key_types_match`, `no_placeholders` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
