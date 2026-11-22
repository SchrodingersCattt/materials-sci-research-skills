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
