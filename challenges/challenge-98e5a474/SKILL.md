---
name: editable-schematic-figure
description: Use for 科研示意图生成与编辑 — deliver an editable schematic figure (SVG source) plus PNG/PDF exports from the supplied material, with every element traceable to a source locator, the supplied template or data respected, and the artifact verified rather than promised.
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

# 科研示意图生成与编辑

Run this on the actual case now and deliver the artifact. Do not describe a figure or a deck you
did not produce, and do not claim a template, a value or a preview that the evidence does not show.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the data, the
  template, the starting deck, the source paper, the workorder, `environment/resources.yaml`. Read
  the actual files; a label is not evidence.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Tool: `"$SKILL_DIR/scripts/make_figure.py"` (`SKILL_DIR` = the real directory of the loaded `SKILL.md`). Python
  3.10+, standard library only: no network, no pip, no plotting package, no python-pptx. A
  LibreOffice renderer is optional and only adds a preview.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Produce an honest artifact
  early and improve it.

## What this deliverable is

Decide the schematic from the supplied material and draw it with an explicit node/edge model: every box, arrow and label exists in the spec with its coordinates and the source it came from, so a human can move a box afterwards. When the case supplies an existing figure to edit, change only the requested elements and say exactly which ones changed.

`chart` for a data figure (bar/line/scatter with optional error bars) and `diagram` for a schematic. Both write an editable SVG, a PNG and a vector PDF.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Read the material and list the facts you will draw or show**, each with the file and locator
   you read it at. Anything the material does not state does not appear in the artifact.
2. **Write the declaration file** (the figure spec or the deck plan). It names the sources, the
   element geometry and the content, so the artifact can be re-derived from it.
3. **Build.**
```
python "$SKILL_DIR/scripts/make_figure.py" chart --spec /app/work/figure.json --out-prefix /app/output/figure1
python "$SKILL_DIR/scripts/make_figure.py" diagram --spec /app/work/diagram.json --out-prefix /app/output/figure1
python "$SKILL_DIR/scripts/make_figure.py" inspect-png /app/output/figure1.png
python "$SKILL_DIR/scripts/make_figure.py" verify --prefix /app/output/figure1 --spec /app/work/figure.json --outdir /app/work/check
```
4. **Verify and look.** The verifier must pass (exit 0). With a renderer present, open the rendered
   PDF/PNG and check hierarchy, clipping and overlap yourself; without one, the missing preview is
   an explicit limitation in `result.json`.
5. **Task-specific checks** — confirm and record each:
1. every node and edge in the spec names the material it came from
2. requested edits touch only the declared elements of the supplied figure
3. the SVG keeps explicit coordinates (no flattened raster)
4. the PNG is inspected: not blank, not clipped, every declared node drawn

6. **Write `result.json`** with the original contract fields: the artifact paths, the preserved
   facts, the element→source map, the change log (what was drawn or changed, what was left out and
   why) and honest uncertainty.
7. **Re-open your own output** before finishing: the verification status is what you claim, the
   artifacts open, and nothing in `result.json` is absent from the reports.

## Failure handling

- An element the material cannot support: leave it out and name it, with what the material would
  need to contain.
- A supplied artifact you must edit: change only the requested elements, keep everything else
  byte-identical, and list what changed.
- Overlap, clipping or overflow: the reports list them by name; fix the layout, do not shrink the
  font until the warning stops.
- No renderer: the editable source and the vector export are still real deliverables.

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

The fixture in `examples/synthetic_case.py` produces the files the commands above consume. Its
values are interface-test values, not case results and not a score. See `MAPPING.md` and
`PROVENANCE.md` in this directory.
