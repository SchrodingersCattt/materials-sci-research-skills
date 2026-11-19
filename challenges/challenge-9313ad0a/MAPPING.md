# Mapping: case requirement → mechanism → verification

Task: turning supplied material into a knowledge map (思维导图). No official scoring claim is made here.

| Requirement | Mechanism | Evidence |
|---|---|---|
| The structure must come from the material | the spec is an explicit tree of nodes, each with `label`, an optional `edge` relationship and an `evidence` locator; nothing is generated that the spec does not declare | `mindmap-spec.json`; build report `nodes[]` with `evidence` per node |
| A reader can check branch by branch | every deep node (depth ≥ 2) without an evidence locator is listed, so an unsupported branch is visible instead of implied | build report `layout.deep_nodes_without_evidence` |
| The picture must be readable, not just drawn | radial layout with **wedge allocation**: each subtree owns an angular span proportional to its leaf count; the radius is derived from the widest box and the smallest leaf wedge; labels wrap at 20 characters | build report `layout.method`, `radius_step`, `nodes[].angle_deg` |
| Nothing may collide or be clipped | axis-aligned box intersection over all node boxes, and a canvas-bounds check | build report `layout.overlap_count`, `layout.nodes_outside_canvas` |
| The exports must be real | editable SVG from an explicit primitive list, a raster PNG (Pillow text when present, else the built-in font) and a vector PDF; each with a recorded hash | build report `out`, `sha256`, `rasterizer`; verification `format.svg/png/pdf` |
| The drawing must actually contain the content | every declared label line is searched for in the produced SVG, and the PNG is decoded and inspected for blank output and edge contact | verification `labels_drawn`, `png_not_blank`, `png_inside_canvas` |
| Honest limits | a missing root is refused; a canvas too small reports its layout problem instead of clipping; inferred edges and aggregated evidence are stated as such | refusal message "no root node"; build report layout problems; `SKILL.md` failure handling |
