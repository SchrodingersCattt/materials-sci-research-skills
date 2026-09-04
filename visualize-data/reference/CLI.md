# visualize-data CLI

Zero-install launcher:

```bash
VD="python /aisi-nas/guomingyu/personal/agent-skills/visualize-data/scripts/visualize_data.py"
```

## Typical strict workflow

```bash
$VD init figures/figure2
$VD contract check --manifest figures/figure2/figure.manifest.json
$VD clipping source --manifest figures/figure2/figure.manifest.json
$VD labels contain --spec figures/figure2/_qa/text_containment.json
$VD qa run --manifest figures/figure2/figure.manifest.json --strict \
  --json-report figures/figure2/_qa/report.json
$VD review init --manifest figures/figure2/figure.manifest.json
# Complete the five review fields, then rerun strict QA.
```

Strict QA rejects configurations that merely make checks pass: output paths
under `_qa`, padded/cropped derivatives declared as source renders, clearance
thresholds below 8 px, blanket edge-touch exceptions, empty safety bands for
multi-panel figures, and placeholder self-review text. A successful command is
reported as automated PASS only; visual acceptance remains a separate gate.

## Exit codes

- `0`: all requested checks passed.
- `1`: valid input with one or more QA failures.
- `2`: invalid input or unavailable required backend.
- `3`: internal CLI error.

Use `visualize_data.py --help`, `<group> --help`, and `capabilities` for the live
command inventory. JSON reports are stable automation inputs; terminal output is
for humans. PNG is read directly. PDF uses `pdftoppm`; SVG uses `rsvg-convert`.
Missing required backends are input errors, never silent skips.

`labels contain` consumes final-render pixel bboxes for each text object and its
owning container. It fails when any text edge crosses the container's declared
inner padding. The same spec is loaded by strict QA through
`checks.text_containment.spec`.
