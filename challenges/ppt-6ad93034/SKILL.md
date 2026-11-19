---
name: template-deck-generation-and-edit
description: Use for 学术 PPT 生成与编辑 — deliver a deck generated into, or edited inside, the supplied template from the supplied material, with every element traceable to a source locator, the supplied template or data respected, and the artifact verified rather than promised.
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

# 学术 PPT 生成与编辑

Run this on the actual case now and deliver the artifact. Do not describe a figure or a deck you
did not produce, and do not claim a template, a value or a preview that the evidence does not show.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the data, the
  template, the starting deck, the source paper, the workorder, `environment/resources.yaml`. Read
  the actual files; a label is not evidence.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Tool: `"$SKILL_DIR/scripts/edit_slides.py"` (`SKILL_DIR` = the real directory of the loaded `SKILL.md`). Python
  3.10+, standard library only: no network, no pip, no plotting package, no python-pptx. A
  LibreOffice renderer is optional and only adds a preview.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Produce an honest artifact
  early and improve it.

## What this deliverable is

Read whether the case asks for generation (bring the paper into the template) or editing (change the supplied deck), then do exactly that: fill the template's own placeholders for new pages, clone a layout-shaped page when a page must be added, and for an edit change only the requested elements while every untouched slide stays byte-identical.

`inspect` reads the template's master, layouts, placeholders and theme, `merge` writes content into them, `check` proves the template survived, `preview` renders a real PDF/PNG when a renderer exists.
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
python "$SKILL_DIR/scripts/edit_slides.py" inspect /input/template.pptx --out /app/work/deck.json
python "$SKILL_DIR/scripts/edit_slides.py" merge --deck /input/template.pptx --plan /app/work/deck-plan.json --outdir /app/work/deck
python "$SKILL_DIR/scripts/edit_slides.py" check --deck /input/template.pptx --output /app/work/deck/edited.pptx --plan /app/work/deck-plan.json --outdir /app/work/deck
python "$SKILL_DIR/scripts/edit_slides.py" preview --deck /app/work/deck/edited.pptx --outdir /app/work/deck/preview
```
4. **Verify and look.** The verifier must pass (exit 0). With a renderer present, open the rendered
   PDF/PNG and check hierarchy, clipping and overlap yourself; without one, the missing preview is
   an explicit limitation in `result.json`.
5. **Task-specific checks** — confirm and record each:
1. the requested mode (generate vs edit) is identified and followed
2. for an edit: untouched slides are byte-identical to the supplied deck
3. new pages inherit a real layout and placeholder structure
4. estimated overflow and any missing placeholder are reported, not hidden

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

Request: build a deck for a supplied paper, using the supplied template.

**Typical low-scoring result**

Six attractive slides whose text was re-typed by hand, so the template's master, layouts and placeholders
are all bypassed; a chart image redrawn from memory; and no record of what changed per page.

Defects: the template inheritance the rubric checks for did not happen; the figure is no longer the
source figure; nothing can be diffed against the source.

**The same deck, compliant**

```json
{
  "source": {"paper": "paper/main.pdf", "template": "template/brand.potx"},
  "pages": [
    {"no": 1, "type": "title", "layout": "Title Slide",
     "placeholders": {"title": "<the paper's own title>", "subtitle": "<the declared authors>"},
     "locator": "p.1"},
    {"no": 2, "type": "outline", "layout": "Title and Content",
     "bullets": ["<3-6 items, each traceable to a section heading>"], "locator": "p.1-2"},
    {"no": 3, "type": "figure", "layout": "Two Content",
     "figure": {"source_page": 5, "reused_as": "the source figure, not redrawn"},
     "caption": "Figure 2 as published; not re-plotted.", "locator": "p.5"}
  ],
  "deviations": []
}
```

Each landing slide is written by filling the layout's own placeholders, so the master, theme fonts and
layout geometry come through unchanged. Every page is recorded in `templates/page-deviation-record.csv`
with expected versus observed and a resolution; the figure page reuses the published figure and says so
instead of redrawing it. The exported PDF is rendered from the PPTX itself, and the render is opened and
checked for overflow before the run ends - that render is the preview the runtime contract asks for.

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
