# QA Subdirectory

This directory is meant to travel with figure-generation work. Copy or symlink
it into a project's figure directory when a figure needs programmatic QA.

Recommended project layout:

```text
manuscript/figures/
├── plot_figN.py
├── figureN.png              # assembled deliverable
├── figureN.pdf              # assembled deliverable
├── _panel_a_raw.png          # intermediate, leading underscore
├── _panel_b_label_qa.png     # intermediate QA artifact, leading underscore
└── qa/
    ├── FIGURE_QA.md
    ├── qa_helpers.py
    └── README.md
```

Use a leading underscore for intermediate panels, debug renders, masks, and QA
artifacts. Use plain filename stems for submission-ready assembled figures. Do
not leave exploratory suffixes such as `_new`, `_final`, `_v2`, or renderer names
on final outputs unless the user explicitly requested variants.

## Recommended CLI wiring

Use the skill CLI rather than copying helper imports into every plot script:

```bash
VD="python /aisi-nas/guomingyu/personal/agent-skills/visualize-data/scripts/visualize_data.py"
$VD init manuscript/figures/figureN
$VD qa run --manifest manuscript/figures/figureN/figure.manifest.json --strict \
    --json-report manuscript/figures/figureN/_qa/report.json
```

The manifest preserves source-panel paths, panel slots, transforms, semantic
colors, physical target size, scientific-integrity declarations, and review hash.
Direct helper imports remain supported for compatibility but are not the primary
workflow.

## Legacy plot-script wiring

Import the helper module near the top of the plot script:

```python
from pathlib import Path
import sys

FIG_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FIG_DIR / "qa"))
import qa_helpers as _qa  # noqa: E402
```

Run validators immediately after drawing or after exporting a panel image. Treat
returned errors as blocking by default:

```python
qa_errors = []
qa_errors += _qa.validate_panel_boundary(
    panel="figure-3 row gap",
    figure_image=exported_rgb,
    rect_px=(0, 820, 2200, 850),
    max_data_pixels=0,
)

if qa_errors:
    raise RuntimeError("\n".join(str(err) for err in qa_errors))
```

## Label Placement Pattern

For object-attached labels, first place labels with the same hard rules that will
later validate them:

```python
records = _qa.whitespace_label_placement(
    image=panel_rgba,
    items=[("A", (122.0, 180.0)), ("B", (240.0, 220.0))],
    cluster_center_px=(180.0, 200.0),
    fontsize_pt=7.0,
    forbidden_rects_px=[legend_bbox_px],
)

errors = _qa.validate_label_panel(
    panel="figure-5b",
    image=panel_rgba,
    records=records,
    cluster_center_px=(180.0, 200.0),
)
if errors:
    raise RuntimeError("\n".join(str(err) for err in errors))
```

The default placement policy is shortest-leader first. It deliberately avoids the
common failure where a label is parked in far whitespace and appears detached
from the object it names.

## Which Helper to Use

- Use `build_data_mask` for simple image-mask checks, footprint metrics, or to
  confirm that a reserved box is empty.
- Use `validate_panel_boundary` for row gaps, column gaps, legend safety bands,
  and stacked schematic lanes.
- Use `whitespace_label_placement` before drawing dense object labels.
- Use `validate_label_panel` after drawing labels and leaders.
- Use `segment_through_mask`, `segments_intersect`, and bbox helpers for custom
  validators that are specific to a figure.

## Human Review Still Required

Automated QA catches pixel-level failures. It cannot know whether the figure
answers the scientific question, preserves required raw content, or reads within
five seconds. After every substantive render, complete the self-review template in
`templates/self_review.md` and rerender after fixes.

## Dependencies

`qa_helpers.py` requires `numpy`. Label placement and distance-map checks require
`scipy.ndimage`. Keep these dependencies project-local; the skill provides the
reference implementation, not an environment manager.
