# Figure manifest

Important figures require `figure.manifest.json`; see
`templates/figure.manifest.json` and `schemas/figure-manifest.schema.json`.
Paths are relative to the manifest directory unless absolute.

Core declarations:

- `figure.canonical_stem`: one final stem across output formats.
- `outputs`: required final files.
- `target`: physical width, QA raster DPI, accepted DPI range.
- `panels[].source`: source raster before composition.
- `panels[].source_stage`: must be `raw-render` in strict mode. A raster cropped,
  padded, or extracted from the final composite is not source-render evidence.
- `panels[].slot`: normalized final-image rectangle `[x0,y0,x1,y1]`, measured
  from the top-left.
- `source_min_clearance_px` and `min_clearance_px`: four-edge clipping gates.
- `allow_touch_edges`: explicit exceptions; empty by default.
- `checks.whitespace`: global and panel occupancy thresholds.
- `checks.boundaries.bands`: declared blank safety regions.
- `checks.text_containment`: declare `applicable`; when true, `spec` points to
  renderer-measured text/container bboxes; when false, record a non-empty reason.
- `checks.colors.semantics`: semantic colors and minimum visible pixels.
- `integrity`: required content, evidence, and approved scientific changes.
- `consistency`, `quantitative`, `deviations`: declarations and evidence.
- `review`: latest render hash and exactly five human-review categories.

Strict-mode anti-bypass rules:

- canonical outputs must point to delivered files, never `_qa/` copies;
- `source_min_clearance_px` and `min_clearance_px` must be at least 8;
- `allow_touch_edges` and `source_allow_touch_edges` require a separately
  approved deviation and are rejected by the default strict gate;
- multi-panel figures require declared boundary safety bands;
- annotation and geometry applicability must be explicit, with machine-readable
  specs when applicable;
- reviews must identify the reviewer, inspected image, physical width, visual
  status, and substantive findings rather than placeholder words.

A strict run fails on missing declarations. A check may be inapplicable only when
the manifest records a reason; absence is not equivalent to inapplicability.
Source panels are mandatory because a final raster with white borders cannot prove
that an upstream renderer did not clip data before composition.
