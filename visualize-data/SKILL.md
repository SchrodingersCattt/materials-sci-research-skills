---
name: visualize-data
description: "Use when creating, revising, composing, or auditing publication-quality scientific figures: plots, structures, raster/vector panels, labels, whitespace, clipping, print scale, semantic colors, scientific integrity, and final output QA."
---

# Visualize Data

Treat figure work as a constrained render-and-QA workflow. Project code owns
scientific rendering; this skill's zero-install CLI owns planning, rasterization,
crop/compose operations, QA, review, and delivery gates.

```bash
VD="python /aisi-nas/guomingyu/personal/agent-skills/visualize-data/scripts/visualize_data.py"
```

## Mandatory Workflow

1. Run `$VD init <figure-work-dir>` and complete `figure_contract.md` plus
   `figure.manifest.json` before substantive plotting.
2. Render canonical outputs and source panels. Important figures require a
   manifest; do not infer camera, scale, semantic colors, or scientific content
   from pixels when renderer metadata can declare them.
3. Run `$VD clipping source --manifest ...` before crop/composition. Every
   raster/3D panel must have four-edge clearance; scene bounds must include all
   data, isosurfaces, periodic components, labels, leaders, and overlays.
4. Use `$VD raster crop|compose|check` for image operations. Crop background
   borders only; preserve aspect ratio and centers; record transforms.
5. Run `$VD qa run --manifest ... --strict --json-report _qa/report.json`.
   Fix every blocking failure, rerender, and repeat. Never substitute selected
   safety-band checks for global whitespace and full-panel clipping checks.
6. Run `$VD review init --manifest ...`, complete exactly five review categories,
   then `$VD review check --manifest ...`. Inspect the exported image at target
   physical size; automated QA is necessary but not sufficient.

## No Self-Certified PASS

- A CLI `PASS` is only evidence that declared checks passed; it is not permission
   to claim that the figure passed visual QA.
- Never weaken a manifest to obtain PASS: no zero composite clearance, blanket
   `allow_touch_edges`, empty boundary bands on multi-panel figures, QA-copy
   outputs, or padded/cropped derivatives presented as raw source renders.
- `review.problems` must contain concrete findings and dispositions. Placeholder
   values such as `checked`, `none`, `ok`, or `pass` are blocking.
- Record the inspected deliverable, physical width, reviewer identity, and
   `visual_status`. If the user disputes the figure, immediately revoke PASS and
   set the review stale; user visual rejection overrides automated results.
- Do not report “QA passed” until both strict checks and post-render visual review
   are substantive. Say “automated checks passed; visual acceptance pending” when
   user acceptance or a scientific presentation choice remains unresolved.
## Figure text and data completeness

Include the information needed to read the data directly in the figure: axis
labels, units, tick values, and legends or scale bars when applicable. Ensure
these match the underlying data and remain legible at the final display size.
For structural panels, include identification or scale labels when necessary
to understand the comparison. Default to a final figure width of one A4 page
(210 mm) or half an A4 page (105 mm), whichever suits the layout; use Arial
at 10 pt for figure text at final display size. Preserve these physical sizes
when exporting or composing panels. An explicit user request takes precedence.
Do not add explanatory paragraphs, narrative
annotations, decorative titles, or crowded text by default; communicate those
explanations in chat or a caption. Respect explicit user requests and inspect
the exported figure for missing, overlapping, or clipped labels.

## Core Gates

- `whitespace audit`: global/panel occupancy, ink bounds, grid, margins, bands.
- `clipping source|composite`: four edges before and after composition.
- `boundary check`: row/column/legend/panel safety bands.
- `labels place|check|contain`: overlap, clearance, leader crossings, data
  traversal, and renderer-measured text containment inside owned boxes.
- Every card, node, legend, or callout with owned text must declare and pass
  `checks.text_containment`; any edge outside the padded container is blocking.
- Manually placed callouts must pass `qa_helpers.validate_leader_clearance`; route
   leaders through real whitespace, never diagonally across unrelated data.
- `geometry check`: isotropic transforms and annotation endpoint tolerances.
- `print check`: physical size and effective DPI.
- `colors check`: declared semantic colors and required presence.
- `consistency|quantitative|integrity|deviations check`: manifest evidence gates.
- `outputs check`: canonical stem, required formats, duplicates and bad suffixes.
- `skill check`: frontmatter, line limit, capability wiring, generated artifacts.
- `strict-policy`: rejects vacuous manifests, derived source evidence, and
   self-certified review records.

## Scientific Integrity

Do not drop required data, disorder branches, symmetry alternatives, failed
cases, uncertainty, or annotations for readability. Do not replace raw content
with cleaned, ordered, smoothed, or filtered content without disclosure and
approval. Do not add unsupported atoms, bonds, links, labels, or quantitative
claims. Do not stretch x and y independently. Any scientific substitution or
unmet rule requires an approved deviation with evidence and follow-up.

## Delivery Gate

Deliver only when canonical files exist, strict QA passes, source and composite
clipping both pass, global whitespace is acceptable, no anisotropic transform is
present, review hash matches the latest render, and deviations are approved. Use
one canonical stem; keep debug artifacts under `_qa/`; forbid `_new`, `_final`,
`_v2`, and `_test` deliverables.
If a check is inapplicable, record the reason in the manifest; never silently
skip it or report a partial run as full PASS.
