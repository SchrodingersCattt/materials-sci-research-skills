# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for the figure tasks
(scientific charts, schematic/pathway diagrams, technical route figures, graphical abstracts). The
renderer is written from scratch in the standard library so the deliverable does not depend on a
plotting package being installed in the evaluation container.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`csv`, `zlib`, `struct`, `xml.sax.saxutils`, `json`, `hashlib`, `math`) | the entire runtime: geometry, SVG, PNG encoder, PDF writer, PNG decoder |
| Pillow (optional) | text rendering for the PNG when installed; the build report records which path ran |
| no matplotlib, no cairosvg, no network | deliberately not used |

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — bar/line/scatter charts each 11/11 checks, diagram 8/8, 33 checks total |
| pixel inspection | the produced PNG is decoded by this module's own reader (all five filter types): `is_blank=false`, ink bounding box inside the canvas, per-band ink coverage reported |
| declaration fidelity | every declared category label is found in the drawing, every declared value has ink at its computed pixel position, every value lies inside the drawn axis |
| negative paths | a spec naming a column the data lacks is refused by name; a value outside the axis fails verification; overlapping diagram nodes are reported |
| layout issues found and fixed while building | an axis label placed at negative x and a footer that ran off the canvas were both caught by the layout check and are now laid out inside the declared margins |

All fixture content is invented for interface testing. No formal case, hidden material or official
score was used to build or validate this skill.

## Boundaries

- The builder draws what the spec declares: no arbitrary vector paths, gradients or embedded
  images, and no automatic choice of chart type — that decision belongs to the agent reading the
  case.
- Text metrics are estimated for the layout check; the rendered PNG is the visual truth.
- The vector PDF uses the base-14 Helvetica font, so the PDF carries no embedded font. A case that
  requires an embedded specific family must state it and supply the font for a renderer to use.
- Resource budget observed: 7 UTF-8 text files, largest 50 KB, 116 KB total — inside the 50-file /
  500 KB-per-file / 2 MB-total skill resource limits.
