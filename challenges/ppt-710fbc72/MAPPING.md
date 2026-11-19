# Mapping: case requirement → mechanism → verification

Task: template-aware deck editing (academic PPT generation, template adaptation and paper→deck
conversion). No official scoring claim is made here.

| Requirement | Mechanism | Evidence |
|---|---|---|
| 模板套用 — the supplied template must be really used, not imitated | `inspect` reads the master, every layout with its placeholder types/indices, the theme fonts and colour slots, and the slide size; `merge` clones a page *of that layout* for new slides and only writes into placeholders the layout actually declares | `deck.json` (layouts, placeholders, theme), `merge-report.json` (`changed_parts`, `added_parts`, `template_parts_unchanged`) |
| 母版/版式/占位符继承可查 | the master, layouts and theme are copied byte-for-byte and every slide keeps pointing at a layout that exists in the package | `slide-check.json`: `master_kept`, `theme_kept`, `template_bytes_kept` (unchanged/drifted counts), `placeholder_inheritance` (dangling list) |
| 页内内容与源论文对得上 | every planned text entry may carry a `source_locator`, and the checker re-reads the produced slides to confirm each declared line is present | `merge-report.json` (`operations[].filled[].source_locator`), `slide-check.json`: `declared_content_present` |
| 版式约束 — fixed text area, overflow, long titles | each text frame's geometry (EMU) is read from the package; the estimated required height is computed from characters, font size and the frame width, with the formula declared in the report | `slide-check.json`: `no_estimated_overflow`, `overflow_estimates[]` (`estimated_lines`, `estimated_height_in`, `box_height_in`) |
| 字体颜色 — theme fonts/colours, no silent fallback | the theme's major/minor latin typefaces and every colour slot are read before and after the edit and must be equal; the preview reports the fonts actually used by the renderer | `slide-check.json`: `theme_kept`; `preview-report.json` (`slides`, `rendered_text`) |
| 交得出 — opens, plays, is editable, and the record allows a re-run | the output is a normal PPTX (presentation + master + layout + slides), an independent validator checks every XML part, relationship target and content type, and the renderer produces a real PDF/PNG | `tests/validate_package.py`, `preview-report.json` |
| Honest limits | a missing placeholder, a missing slide to clone, an estimated overflow and a missing renderer are all reported as named exceptions instead of being hidden | `merge-report.json` (`missing_placeholders`, `status`), `slide-check.json` (`overflow_estimates`), `preview-report.json` (`note`) |
