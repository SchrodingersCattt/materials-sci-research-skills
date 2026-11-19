---
name: graphical-abstract-figure
description: Use for Graphical Abstract（图形摘要） — deliver a graphical abstract: one self-contained figure with a caption from the supplied material, with every element traceable to a source locator, the supplied template or data respected, and the artifact verified rather than promised.
---

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

# Graphical Abstract（图形摘要）

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

Compress the supplied study into one figure without adding a claim it does not support: the flow is declared as nodes and edges, quantitative statements appear only where the material reports them, and anything about mechanism, causality or long-term behaviour that the material does not establish is left out or marked as a hypothesis in the caption.

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
1. no value or claim appears that the material does not report
2. the caption states the reading conditions and any comparison the figure implies
3. the flow is readable as one figure (no overlap, nothing clipped)
4. the editable SVG is delivered alongside PNG and PDF

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

## Diagram identity guard
Default node position is applied consistently to rendering. Node IDs are unique nonempty strings, geometry finite with positive sizes, and every edge endpoint must name a node before any export. Invalid edges are rejected rather than silently omitted. This does not guarantee label layout or scientific correctness and does not diagnose platform evaluation_error.

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

