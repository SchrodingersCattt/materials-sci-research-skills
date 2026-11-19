# declared-data-figure-builder

A skill for the figure/chart/diagram tasks: a supplied data file becomes a figure whose every
element is declared, delivered as an editable SVG plus a real PNG and a vector PDF, with the
pixels inspected rather than assumed.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/make_figure.py` | the runtime: `chart`, `diagram`, `inspect-png`, `verify` |
| `MAPPING.md` | case requirement → mechanism → verification |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | builds the synthetic data, chart spec and diagram spec |
| `tests/run_checks.py` | bar/line/scatter + diagram, plus three negative paths |

## Requirements

Python 3.10+ and the standard library only. No network, no pip, no matplotlib. Pillow is used for
text when it happens to be installed; otherwise the module rasterizes with its own primitives and
a built-in 5x7 font. PNG and the vector PDF are written by this module in both cases.

## Use

```
python scripts/make_figure.py chart --spec work/figure.json --out-prefix out/figure1
python scripts/make_figure.py diagram --spec work/diagram.json --out-prefix out/figure2
python scripts/make_figure.py inspect-png out/figure1.png
python scripts/make_figure.py verify --prefix out/figure1 --spec work/figure.json --outdir work/check
```

Each build writes `<prefix>.svg`, `<prefix>.png`, `<prefix>.pdf` and `<prefix>.build-report.json`
(hashes, rasterizer, axis, every drawn mark, layout issues). `verify` writes
`<prefix>.verification.json`; exit code `3` means a check failed.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

Positive path: bar, line and scatter charts plus a diagram, each verified (11 checks for a chart,
8 for a diagram). Negative paths: a spec naming a column the data lacks must be refused, a value
outside the drawn axis must fail verification, and overlapping diagram nodes must be reported.

## Scope and limits

- The builder draws what the spec declares. Category order, series order and the axis range are
  computed from the data; a case that needs a specific order or range must state it.
- Text advance is estimated (0.62 x font size per character) for the layout check; the rendered
  PNG is the visual truth, and `pillow` text metrics differ slightly from the estimate.
- Diagrams support nodes, labelled edges, a legend and a caption. They are not a general vector
  illustration tool: no arbitrary paths, gradients or embedded images.
- The built-in rasterizer's text is a 5x7 bitmap font, which is legible but plain; with Pillow
  present the text uses a real font. The build report says which path ran.
- Not an official score; the verification proves declaration-faithful drawing, not scientific
  judgement about which figure to draw.

## Maintenance

One standard-library script. Extend the chart kinds, the layout checks and the pixel inspection,
not the dependency list, and keep `tests/run_checks.py` green — including its three negative paths.
