# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for the mind-map task,
on top of the shared standard-library primitive layer (`make_figure.py`) so the deliverable depends on
neither a graph library nor a plotting package nor a pinned `doc-forge` installation.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`math`, `json`, `hashlib`, `re`, `pathlib`) | the entire runtime |
| `make_figure.py` (same directory) | the shared SVG/PNG/PDF emitters and the PNG inspector |
| Pillow (optional) | text rendering for the PNG when installed; the build report records the path used |

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — 14 nodes, 5 branches, 0 overlaps, nothing outside the canvas, 10/10 checks pass |
| layout on the fixture | wedge allocation puts each branch in its own angular span; the widest box and the smallest leaf wedge set the radius, so sibling branches do not cross |
| evidence discipline | every node at depth ≥ 2 in the fixture carries a locator, and the build report would list any that did not |
| negative paths | a spec with no root is refused with a named message; a canvas too small for the tree reports `nodes_outside_canvas`/overlaps instead of clipping silently |

The first layout implementation fanned children around the parent's absolute angle and produced four
overlapping pairs on the fixture; the wedge-allocation rewrite removed them, and the layout check in
the build report is what caught it.

## Boundaries

- Radial layout with straight polyline edges. No curved routing, bundling or manual pinning.
- The layout check is geometric plus a decoded-pixel inspection; it is not a typographic review.
- Not an official score, and not a judgement about whether the knowledge structure is scientifically
  the right one — that stays with the author and the reviewer.
- Resource budget observed: 7 UTF-8 text files, largest 50 KB (the shared primitive layer),
  118 KB total — inside the 50-file / 500 KB-per-file / 2 MB-total skill resource limits.
