# source-anchored-mindmap

A skill for the mind-map task: the supplied material becomes a radial knowledge map whose structure is
laid out by wedge allocation (so branches never cross), whose deep nodes carry the evidence locator
they came from, and which exports an editable SVG plus a real PNG and vector PDF.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/make_mindmap.py` | the runtime: `build` (layout + draw) and `verify` |
| `scripts/make_figure.py` | the shared primitive layer (SVG/PNG/PDF emitters, PNG inspector) |
| `MAPPING.md` | case requirement → mechanism → verification |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | the synthetic tree used by the self-test |
| `tests/run_checks.py` | positive path plus two negative paths |

## Requirements

Python 3.10+ and the standard library only. No network, no `pip install`, no graph library. Pillow is
used for text when installed; otherwise the shared layer rasterizes with its own primitives.

## Use

```
python scripts/make_mindmap.py build  --spec work/mindmap.json --out-prefix out/mindmap
python scripts/make_mindmap.py verify --prefix out/mindmap --spec work/mindmap.json --outdir work/check
```

`build` writes `<prefix>.svg`, `<prefix>.png`, `<prefix>.pdf` and `<prefix>.build-report.json` (every
node with its coordinates, angle and evidence, the chosen radius, and any layout problem). `verify`
writes `<prefix>.verification.json`; exit code `3` means a check failed.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

Positive path: a 14-node, 5-branch fixture lays out with zero overlaps, nothing outside the canvas,
every deep node carrying evidence, and 10/10 checks pass. Negative paths: a spec with no root is
refused, and a canvas too small for the tree reports the layout problem instead of clipping silently.

## Scope and limits

- The layout is radial with wedge allocation and wrapped labels. Very wide labels at depth 3+ widen
  their boxes, which raises the derived radius; a tree that still does not fit is reported as
  `nodes_outside_canvas` rather than shrunk.
- Edges are straight polylines through the midpoint; no curved routing or bundling.
- The layout check is geometric (box intersection, canvas bounds) plus a decoded-pixel inspection
  (blank, clipped). It is not a typographic review.
- Not an official score, and not a judgement about whether the knowledge structure is the right one.

## Maintenance

One standard-library script plus the shared primitive layer. Extend the layout (for example a
non-radial mode), not the dependency list, and keep `tests/run_checks.py` green — including its two
negative paths.
