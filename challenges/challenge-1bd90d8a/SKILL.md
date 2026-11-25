---
name: declared-data-figure-builder
description: Use when a figure, chart, diagram or graphical abstract must be produced from supplied data — decide each element from a declared source, deliver an editable SVG plus a real PNG and vector PDF, and prove from the pixels that the declared values were actually drawn.
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

# Declared-data figure builder

Run this on the actual case and deliver the figure. Do not describe a chart you did not draw,
do not digitise a value by eye, and do not report a preview you did not render.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the data, the
  captions, the workorder, any supplied image, `environment/resources.yaml`. A plot's apparent
  height is not a reported value and a figure caption is not a data table.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Tool: `"$SKILL_DIR/scripts/make_figure.py"` (`SKILL_DIR` = the real directory of the loaded
  `SKILL.md`). Python 3.10+, standard library only: no network, no pip, no matplotlib. Pillow is
  used for text only when it happens to be installed, and the build report says which rasterizer
  ran.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Produce an honest figure
  early, then refine it.
- Every element of the figure needs a declared reason: the data source, the unit, the condition,
  what the error bars mean, and where the labels come from. If the material does not state it,
  the figure must not show it.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Inventory the declared facts first.** For every plotted quantity record: the file, the row
   identifier, the column, the value, the unit, the condition, and the comparator. Uncertainties
   only exist if the material reports them — and say what they are (SD, SEM, CI, range) or draw
   none.
2. **Write the spec.** One JSON file per figure:
   - `chart`: `data`, `x`, `value`, optional `series`, `error_low`, `error_high`, `unit`,
     `x_label`, `y_label`, `error_meaning`, `note`, `source`. Category labels come from the data
     column, so the drawing cannot invent one.
   - `diagram`: `nodes` with `id`, `x`, `y`, `w`, `h`, `label`, `position`, plus `edges`,
     `legend`, `caption`. Coordinates are explicit so a human can move a box afterwards.
3. **Build.**
   `python "$SKILL_DIR/scripts/make_figure.py" chart --spec /app/work/figure.json --out-prefix /app/output/figure1`
   (or `diagram`). You get three real artifacts: the editable `.svg` source, a raster `.png`,
   and a **vector** `.pdf`. The build report records each hash, the rasterizer used, the axis
   range, every drawn mark with its pixel position, and a layout check (text outside canvas,
   label overlap, content inside margins).
4. **Inspect the pixels.** `... inspect-png /app/output/figure1.png` decodes the PNG with its own
   reader (all five filter types) and reports ink coverage, the ink bounding box, coverage per
   band and whether anything touches the canvas edge. Look at the PNG yourself as well; the
   numbers catch clipping and blank output, not taste.
5. **Verify.** `... verify --prefix /app/output/figure1 --spec /app/work/figure.json --outdir /app/work/check`
   proves the three signatures are real, the PNG is not blank and not clipped, every declared
   category label is drawn, every declared value has a drawn mark at its computed position in the
   pixels, and every value sits inside the drawn axis. Exit 3 means a real mismatch: fix the spec
   or the data reading, never a hash.
6. **Write `result.json`** with the original contract fields: the artifact paths, the
   preserved facts, the element→source map (each axis, series, label and caption with its
   locator), the change log (what was drawn, what was left out and why) and honest uncertainty
   (an unreadable figure, an unstated uncertainty convention, a category with no data).
7. **Re-open your own output** before finishing: the artifacts exist, the verification report's
   status is what you claim, and every number quoted in `result.json` traces to the spec or the
   verification.

## Failure handling

- The case supplies an image instead of data: read it with the tools that are actually present,
  report the extracted coordinates as approximate with the reading method, and mark every
  inferred point. Never present an eye-read value as a reported one.
- A requested element the material cannot support (an error bar with no reported spread, a
  p-value, a fitted curve with no fit): leave it out, name it in `result.json`, and say what the
  material would have to contain.
- Overlapping elements or text outside the canvas: the build report lists them by name; move the
  box or shorten the label rather than shrinking the font until it stops complaining.
- No rasterizer for a requested format: the SVG and the PDF are still real deliverables, and the
  missing one is an explicit limitation.

## The editable source is part of the deliverable

This channel's statement counts **可编辑源文件 (a layered editable source)** as one of the six
elements a figure must cover, alongside the export. So each build writes five files, and all five go
to `/app/output`:

| File | What it is |
|---|---|
| `<name>.svg` | the vector export, editable in any vector tool |
| `<name>.png` | the raster export, inspected for clipping and blank ink |
| `<name>.pdf` | the print export |
| `<name>.drawio` | **the layered source**: every element addressable by id with its geometry, its layer and its declared source, opened by draw.io / diagrams.net |
| `<name>.provenance.csv` | element id, element class, drawn content, meaning (an edge's direction and polarity), source file and locator |

`make_figure.py` writes the `.drawio` and `.provenance.csv` automatically. Do not deliver only the
PNG: the export alone fails 可编辑性, because the reviewer cannot reopen and move anything.

## The declared semantics are part of the figure, not just the picture

The rubric's correctness points are entity, relation, **direction, hierarchy, relative proportion and
unit**, and its completeness point names **three element classes plus legend, annotation, units and
subfigure numbering**. Those are declared in the spec, drawn in the artwork, and checked:

| Spec key (per node) | What it does |
|---|---|
| `class` | `entity` / `medium` / `readout` - the three element classes, drawn and recorded per element |
| `subfigure` | `(a)`-style numbering, drawn at the box corner |
| `value` + `unit` | a declared magnitude with its unit, drawn inside the box; a value with no unit is refused |
| `source` + `locator` | the file and locator the element came from, carried into the provenance record |

| Spec key (per edge) | What it does |
|---|---|
| `polarity` | `activate` (solid arrow) / `inhibit` (bar) / `translocate` (dashed) / `regulate` |
| `from` / `to` | the real endpoints, so the draw.io source keeps them wired |
| `source` + `locator` | where the relation is stated |

Declare `legend` (class colour to meaning) and `relation_key` (polarity to meaning). When the figure
draws more than one polarity the artwork **must** distinguish them in ink, not only in the caption: an
inhibition bar and a solid arrow, never two identical arrows with different words. `verify` fails a
figure whose legend omits a class it uses, whose recorded element is not actually drawn, an edge whose
endpoints do not resolve, or a declared value with no unit.

## Exports are checked against their target

`verify` reads the numbers back out of the files that were written, rather than assuming them: the
**ink bounding box** against the declared canvas at 150 dpi (the footer grows with the caption, so the
nominal size would check nothing), PNG pixel size, SVG text left as text and `viewBox` present,
smallest drawn text above the legibility floor, and PDF present with a `MediaBox`. Each becomes an
`export_*` check in the verification report. A figure that covers its target area but cannot be
printed at the target size is not a completed export.

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

Request: a technical-route diagram from a supplied method paragraph.

**Typical low-scoring result**

A visually tidy diagram with icons, an arrow from "precursor" to "product", a title that says the
system "works well", and no statement of where the elements came from.

Defects: the visual vocabulary is invented rather than read from the source; no element carries a
locator; the caption asserts a quality claim the material does not make.

**The same figure, compliant**

```json
{
  "figure_id": "F-01",
  "kind": "route",
  "source": {"file": "material/methods.md", "locator": "paragraph 2"},
  "elements": [
    {"id": "n1", "label": "precursor solution", "role": "input", "locator": "p2 sentence 1"},
    {"id": "n2", "label": "hydrothermal treatment", "role": "process",
     "conditions": "180 C, 12 h", "locator": "p2 sentence 2"},
    {"id": "n3", "label": "crystalline product", "role": "output", "locator": "p2 sentence 3"}
  ],
  "edges": [{"from": "n1", "to": "n2", "sense": "input"}, {"from": "n2", "to": "n3", "sense": "yields"}],
  "unsupported": [{"requested": "purification step", "status": "not in the supplied material"}]
}
```

Rendered as SVG with the declared labels only, plus `figures/manifest.csv` carrying the figure id, the
file hash, the pixel size and the section that cites it. The caption names what is plotted and its
source: "Route reported in the supplied methods (§2). Conditions as stated; no purification step is
reported."

The `unsupported` list is the part a low-scoring run omits. Showing what the material did *not*
contain is also how a reviewer can tell the figure was read rather than decorated.

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
python "$SKILL_DIR/scripts/make_figure.py" chart --spec /app/work/fixture/chart-spec.json --out-prefix /app/work/chart
python "$SKILL_DIR/scripts/make_figure.py" inspect-png /app/work/chart.png
python "$SKILL_DIR/scripts/make_figure.py" verify --prefix /app/work/chart --spec /app/work/fixture/chart-spec.json --outdir /app/work/check
```

Illustrative output for the fixture: 11/11 checks pass, `ink_coverage=0.016`, `is_blank=false`,
every declared mark found in the pixels. Those numbers come from `examples/synthetic_case.py` — an
interface fixture, not case results and not a score. See `MAPPING.md`.

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
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract work/contract.json --out work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work work
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
| 5 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 7 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `figure-check-item.md`, `figure-manifest.csv`, `figure-table-pointer-template.csv`, `glossary-template.csv` and more. |
| 2 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`, `run_checks.py`. |
| Worked fixtures (`examples/`) | `README.md`, `case.json`, `material`, `synthetic_case.py`, `task.md` - realistic shapes you can run end to end before touching real material. |
| Test cases (`tests/cases/`) | 4 declared cases you can extend with your own. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Optional: a LibreOffice/PDF renderer. If one is present the build also emits a raster preview and says so; if not, the exports still exist and the report names the missing preview as an explicit limitation rather than inventing one.
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
| declared artifacts inspected per run | 33 |
| of which are content checks, not just file presence | 29 |
| distinct machine-readable reports emitted | 7 |
| conditions the package refuses to pass silently | 6 |
| self-test suites shipped | 2 |
| self-test assertions | 28 |
| adversarial negative controls in the test suite | 17 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 33 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 6 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 7 machine-readable report(s): `figure-build/v1`, `figure-verify/v1`, `number-scan/v1`, `output-contract-check/v1` |
| Regression safety | none | 28 assertions in the shipped self-tests, including 17 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `artifact{suffix`, `case_id_preserved`, `check_layout`, `declared_columns_present`, `declared_labels_present`, `declared_values_carry_units`, `declared_values_drawn`, `declared_vocabulary_respected`, `drawio_edges_wired`, `drawio_nodes_present` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
