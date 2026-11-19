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

This channel's statement counts **?????? (a layered editable source)** as one of the six
elements a figure must cover, alongside the export. So each build writes five files, and all five go
to `/app/output`:

| File | What it is |
|---|---|
| `<name>.svg` | the vector export, editable in any vector tool |
| `<name>.png` | the raster export, inspected for clipping and blank ink |
| `<name>.pdf` | the print export |
| `<name>.drawio` | **the layered source**: every element addressable by id with its geometry, opened by draw.io / diagrams.net |
| `<name>.provenance.csv` | element id to source file and locator, for the ??????? requirement |

`make_figure.py` writes the `.drawio` and `.provenance.csv` automatically. Do not deliver only the
PNG: the export alone fails ?????, because the reviewer cannot reopen and move anything.

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
