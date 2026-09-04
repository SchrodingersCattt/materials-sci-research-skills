# Figure QA Acceptance Criteria

This document is the binding acceptance test for figures created with the
`visualize-data` skill. It is intentionally renderer-agnostic: the checks apply
to line plots, scatter plots, heatmaps, structural panels, raster composites,
and mixed multi-panel figures.

A figure is not done when the script runs. It is done when the exported image
passes programmatic checks where possible and a written human self-review where
judgement is still required.

## 1. Universal Rules

### 1.1 Decorations live in whitespace, never on data

Axis keys, legends, scale bars, compass roses, inset labels, equation overlays,
and panel letters must sit in real background whitespace after the data layer is
rendered.

Suggested programmatic test:

- Build a `data_mask` from the exported RGB/RGBA image: any non-background pixel
  is data ink.
- Dilate the mask by 1-4 px to catch anti-aliased edges.
- The decoration bbox must overlap zero data pixels, or the reserved region must
  be at least 95 percent background pixels.
- A halo or white patch is not an exception. The underlying region must still be
  empty enough that the decoration is not hiding data.

### 1.2 Cross-panel consistency

The same element type must render identically across comparable panels:

- same palette for the same semantic class;
- same font family, text size, marker style, line width, and alpha convention;
- same camera, axis limits, viewport, binning, or physical scale when the panels
  are meant to be compared directly.

A convention that is clean in one panel and overlaps data in another is still a
failure. Fix the layout or reserve a dedicated whitespace band.

### 1.3 Print-scale legibility

Inspect the exported figure at the intended physical size:

- single-column width is approximately 88 mm;
- double-column width is approximately 180 mm;
- every text element should be at least 7 pt at final size;
- captions, axis labels, tick labels, and legends should usually be at least 8 pt;
- raster content should usually land between 200 and 600 dpi at final size.

Do not rely on notebook zoom or a full-screen image viewer. A figure that is
readable only at 300 percent zoom has failed.

### 1.4 Truncated axes are explicit

If a bar chart or quantitative axis does not include the natural baseline, the
caption or panel label must state the truncation. QA should flag missing caption
language for known truncated panels.

### 1.5 Information density has a ceiling

A panel with more than 8 annotations in less than 2 square inches of plot area is
at risk. The default response is to enlarge the panel, reduce nonessential
labels, split the panel, or move secondary annotations elsewhere. Do not weaken
clearance thresholds to force a crowded panel through QA.

### 1.5.1 Embedded prose is a failure mode

Plot panels are not captions. Explanatory sentences, methods notes, provenance,
scope limitations, and validation metrics belong in the caption or manifest.
Default to no more than two short callouts per panel, normally 1–4 words each.
Multi-line text is reserved for compact symbol definitions, not paragraphs.
If a scientific limitation is essential, encode it structurally (for example,
omit unsupported connections and label the axis/legend accurately) rather than
adding a paragraph inside the plotting area.

### 1.6 Panel-boundary clearance

Every multi-row figure should declare row-gap safety bands in figure pixel or
physical coordinates. Every multi-column row should likewise declare column-gap
safety bands unless the gap is intentionally occupied by a legend or row label.

Acceptance:

- The safety band should be at least 99 percent background pixels.
- Text, tick labels, legends, data marks, spines, and panel letters from adjacent
  panels must not invade the band.
- If a narrow letter column is intentionally carved out of the band, document it
  and check the remaining band.

Use `qa_helpers.validate_panel_boundary` for this check whenever the figure has
rows, columns, stacked icon lanes, or dense insets.

### 1.7 Within-panel row isolation

Panels that stack schematic rows, icon ladders, structure rows, or repeated
small multiples must keep each row's ink inside its own vertical slot wherever
that row owns the ink column.

Acceptance:

- Declare the between-row strips after rendering.
- Check those strips in exported pixel space, not only in axes coordinates.
- Shared columns, fan-out arrows, or intentional connectors may be excluded, but
  the exclusion must be explicit.

This catches the failure mode where adjacent rows visually merge and the mapping
between row label, icon, and quantitative result becomes unreadable.

## 2. Annotation Placement

### 2.1 Hard rules

For labels, arrows, leader lines, atom/site labels, peak labels, and scatter
labels, programmatic QA should fail the build when any of these occur:

| Rule | Threshold |
|---|---|
| Label bbox overlaps data mask | 0 px overlap |
| Label bbox overlaps another label bbox | 0 px overlap |
| Edge distance between sibling labels | at least 0.4 x text height |
| Label center distance to nearest data pixel | at least 6 px at 600 dpi, or the project-calibrated equivalent |
| Leader direction versus outward target direction | cosine >= -0.3; only clear u-turns are rejected |
| Leader line crosses another leader | 0 crossings |
| Leader line enters another label bbox | 0 crossings |
| Leader line passes through non-target data | 0 mask hits outside target and label endpoints |
| Leader length | at most 4 x text height unless explicitly justified |

Use `qa_helpers.validate_label_panel` when a panel has object-attached labels or
leaders.

For a single manually positioned callout, use
`qa_helpers.validate_leader_clearance`. A leader that crosses a scatter cloud,
frontier, error bar, or any non-target mark is blocking even when the label
itself occupies whitespace. Prefer a nearby empty corner—often the lower-left
for lower-left Pareto targets—and a short outward leader.

### 2.2 Text owned by boxes

Text visually owned by a card, node, legend box, callout, or badge must remain
fully inside that container after the final renderer draw. This is a separate
gate from canvas clipping and text-text overlap.

| Rule | Threshold |
|---|---|
| Text bbox outside its padded container bbox | 0 px on every edge |
| Inner padding | at least 2 px at QA raster scale, or a larger project value |
| Measurement | final renderer bboxes; character-count estimates are forbidden |

For Matplotlib, draw the canvas first and export both
`Text.get_window_extent(renderer)` and the owning patch's
`get_window_extent(renderer)`. Run `labels contain --spec ...`; strict QA must
also declare `checks.text_containment`. If a line does not fit, enlarge the box,
wrap or shorten the wording, or restructure the panel. Do not shrink body text
below 7 pt or mark the overflow as a non-blocking review comment.

### 2.3 Placement scoring policy

The placement algorithm should be shortest-leader first, with whitespace
clearance as a hard floor and tie-breaker. Do not choose a far-away empty corner
when a nearby valid label slot exists.

Recommended candidate filter order:

1. Reject bboxes that overlap data or forbidden rectangles.
2. Reject bboxes that overlap or crowd sibling labels.
3. Reject leaders that u-turn, cross leaders, enter sibling labels, or pass
   through non-target data.
4. Reject leaders longer than the maximum allowed length.
5. Require minimum data-mask clearance.
6. Among surviving candidates, maximize `-leader_length + small_clearance_bonus`.

Use `qa_helpers.whitespace_label_placement` as the default reference pattern.

### 2.4 Fallback policy

If strict placement cannot place every label, the script must raise or return a
blocking `QAError` with the failing label name. Forbidden fallbacks:

- silently placing a label radially regardless of collisions;
- reducing text size until the label becomes unreadable;
- hiding data to make room;
- relaxing thresholds without documenting the deviation.

Acceptable responses are to enlarge the panel, drop labels the figure does not
need, split the panel, or explicitly record a justified deviation in Section 6.

## 3. Axis Keys, Triads, and Compass Roses

### 3.1 Equal length in display pixels

Direction arrows in an axis key must have equal display-pixel length unless the
figure explicitly encodes vector magnitude. Equal axes-fraction offsets are not
enough because non-square axes distort the rendered arrow lengths.

### 3.2 Anchor outside data

Triads and compass roses belong in a reserved whitespace strip or outside the
data extent. A triad placed inside a panel is acceptable only if its bbox clears
the data mask under Rule 1.1.

### 3.3 Semantics are explicit

For crystallographic, map, and embedding panels, state whether the key shows
basis directions, screen directions, physical axes, or relative magnitudes. Do
not let equal-length arrows imply equal lattice constants or equal physical
scales unless that is true.

## 4. Bar, Scatter, Dumbbell, and Quantitative Panels

- Tick labels should stay between 0 and 60 degrees and must not overlap adjacent
  ticks or panels.
- Grouped bars should use separator lines or bracket annotations, not floating
  group text that competes with data.
- Axis labels must include units when units exist.
- Markers should usually be at least 5 pt^2 with edge widths at least 0.5 pt.
- Error bars, confidence intervals, sample sizes, and fit equations must be
  represented consistently across comparable panels.
- Any jitter, binning, smoothing, normalization, or clipping that changes the
  visual interpretation must be explicit in code comments, captions, or methods.

## 5. Process for Every Substantive Render

1. Fill a figure contract before plotting.
2. Render the real deliverables, not only notebook previews.
3. Run applicable programmatic QA helpers.
4. Convert vector deliverables to a PNG at journal/display width and inspect the
   actual physical-size image.
5. Run the 5-problem human self-review from `templates/self_review.md`.
6. Fix every blocking issue, rerender, and repeat the QA loop.
7. Only deliver when the requested filenames exist and no unwanted exploratory
   variants remain.

Programmatic QA is not optional for important figures. Passing it is necessary
but not sufficient.

## 6. Outstanding Deviations Log

Any figure that cannot satisfy a rule must carry a short, explicit deviation log
near the plot script or in a project-local QA file:

| Panel | Rule | Justification | Follow-up |
|---|---|---|---|
|  |  |  |  |

A deviation without a justification and follow-up is not accepted. A deviation
that changes the scientific content needs user approval.

## 7. Geometry-Bearing Annotations

Any annotation whose endpoint, length, or angle must coincide with rendered data
must be drawn in the same coordinate system as the data whenever possible. This
includes distance bars, bonds, contacts, arrows between structures, peak markers,
polygon outlines, and object-anchored highlights.

Forbidden pattern:

- Render objects in one coordinate system, then hand-place object-aligned lines
  in axes-fraction or figure-fraction coordinates as if visual agreement were a
  proof of correctness.

Required QA:

- Verify each annotation endpoint maps to its intended object within a declared
  pixel or data-space tolerance.
- If the renderer performs hidden margin, camera, or aspect fitting, prefer
  native renderer annotations or exported data-coordinate overlays rather than
  reverse-engineered manual projection.
- If exact endpoint verification is impossible, state the limitation and keep
  the annotation qualitative rather than quantitative.

## 8. Scientific Integrity

Readability fixes must not alter scientific content unless the user explicitly
approves and the caption or code states the substitution.

Do not:

- delete required disorder branches, symmetry alternatives, data points, error
  bars, failed cases, or sample groups for readability;
- replace raw or experimental structures with cleaned or ordered models without
  disclosure;
- add synthetic atoms, labels, bonds, or visual marks that imply unsupported
  chemistry, geometry, or statistics;
- construct molecular or object identity from a coordinate window when a graph,
  provenance table, grouping column, or source label exists;
- draw cross-branch or cross-category connections that the source data do not
  support;
- non-proportionally stretch a raster or structure image to fill a slot.

When a panel looks too small, first identify whether the wasted area comes from
the renderer viewport, raster export margin, compositing layout, or true data
aspect ratio. Fix the cause; do not stretch the image independently in x and y.

## 9. Clipping Is a Two-Stage Blocking Check

Every raster, structural, and 3D panel must pass clipping checks both **before**
crop/composition and **after** final composition.

Source-render acceptance:

- inspect top, bottom, left, and right independently;
- require the manifest's minimum background clearance on every edge;
- compute scene bounds from all rendered atoms, bonds, data, isosurfaces,
  periodic components, labels, leaders, and overlays—not only nominal axes,
  unit-cell corners, or primary data;
- any intentional edge touch requires a manifest allowlist entry;
- fail if content was already truncated upstream, even when the exported source
  raster has a later-added white border.

Composite acceptance:

- retain the source mask, crop rectangle, isotropic scale, offset, and slot;
- prove that the full source mask maps inside the final panel slot;
- recheck all four final slot edges and annotation extents;
- never treat final-image whitespace as evidence that source rendering was
  complete.

Cropping is permitted only after source clipping passes. A visible lobe, marker,
glyph, error bar, line, or surface cut by an edge is a blocking failure regardless
of whitespace, occupancy, or other QA results.
