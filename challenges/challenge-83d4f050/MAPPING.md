# Mapping: case requirement → mechanism → verification

Task: 生物机制图与通路图.

| Requirement | Mechanism | Evidence |
|---|---|---|
| the figure comes from declared data or a declared structure | chart/diagram spec names the data file, columns and coordinates; the builder refuses an undeclared column | build report `data`/`nodes`, refusal message naming the missing column |
| units, conditions and error-bar meaning are stated | `unit`, axis labels, `error_meaning`, `note`, `source` are drawn and recorded | build report `error_bar_meaning`, `declared_source`; axis label and footer in the SVG |
| the reader can check the figure against the source | every drawn mark is recorded with its value and pixel position; verification re-decodes the PNG and looks for ink at each position | verification `declared_values_drawn`, `declared_labels_present`, `values_inside_axis` |
| layout quality is measured | text advance is estimated; the PNG decoder reports ink coverage, bounding box and edge contact | build report `layout.issues`; `inspect-png` (`ink_coverage`, `is_blank`, `touches_edges`) |
| a real editable deliverable | explicit-coordinate SVG plus PNG and a vector PDF, each with a recorded hash | build report `out`, `sha256`, `rasterizer` |
| honest limits | unsupported elements, overlaps, clipping and a missing rasterizer are named | `layout.issues`, `is_blank`/`touches_edges`, `SKILL.md` failure handling |

Task-specific requirements:

- every edge declares its evidence class (measured / reported / hypothesised)
- hypothesised links are visually and textually distinguishable
- component names match the material
- the PNG is inspected and the layout issues list is empty
