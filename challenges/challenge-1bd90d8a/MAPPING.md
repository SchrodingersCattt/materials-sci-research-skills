# case requirement → mechanism → verification

Task: declared-data figure production (charts, diagrams, graphical abstracts). No official
scoring claim is made here.

| Requirement | Mechanism | Evidence |
|---|---|---|
| The figure must come from declared data, not from an eye-read value | the spec names the data file and the columns for category, value, series and error; the builder refuses a column the file does not have and reads every value with `csv` | build report `data` (path, rows, categories, series, unit); refusal message naming the missing column |
| Units, conditions and error-bar meaning must be stated | `unit`, `x_label`, `y_label`, `error_meaning`, `note` and `source` are spec fields that are drawn into the figure (axis label and footer) and copied into the report | build report `error_bar_meaning`, `declared_source`; SVG axis labels and footer text |
| An editable source, not a screenshot | the SVG is written from an explicit primitive list with real coordinates, so a human can move a label or a node afterwards | `.svg` artifact with `sha256` |
| Real exports | a raster PNG (Pillow text when available, otherwise this module's own rasterizer and 5x7 font) and a **vector** PDF using base-14 Helvetica | build report `rasterizer`; verification checks that each file starts with its real signature |
| 核得了 — the reader can check the figure against the data | every drawn mark is recorded with the value it encodes and its pixel position; verification re-decodes the PNG and looks for ink at each recorded position, and confirms every declared category label appears in the drawing | verification `declared_values_drawn`, `declared_labels_present`, `values_inside_axis` |
| Layout quality is measured, not asserted | the builder computes text advance, flags text outside the canvas, overlapping labels and content outside the margins; the PNG decoder independently reports ink coverage, ink bounding box and edge contact | build report `layout.issues`, `fits_inside_margins`; `inspect-png` (`ink_coverage`, `ink_bbox`, `is_blank`, `touches_edges`, `ink_by_band`) |
| Honest limits | unsupported data, an unreadable source image, an element the material cannot support and a missing rasterizer are all named rather than faked | `SKILL.md` failure handling; layout issues and blank/clipped pixel reports |
