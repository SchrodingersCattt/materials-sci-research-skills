# Mapping: case requirement → mechanism → verification

Task: 写作17｜科研成果转化写作.

| Requirement | Mechanism | Evidence |
|---|---|---|
| read the supplied material, not a label | the findings ledger records a source locator for every fact used | `quantity-report.json`: `sources[]`, `mappings[]` |
| every number traceable to a supplied source value | declared quantity id or declared compatible-unit calculation per number, re-read from the source row | checks `source_version_*`, `source_row_unique_*`, `actual_value_*`, `actual_unit_adjacent_*` |
| no undeclared number anywhere in the deliverable | every numeric token in a section must fall inside a declared quote | check `all_detected_section_numbers_covered_<section>` |
| figure/table pointers are references, not measurements | reference numbers are declared separately and must point at a locator that exists | checks `reference_marker_*`, `reference_locator_exists_*` |
| uncertainty stated rather than implied | required qualifiers are literal requirements of the declared quote | check `literal_qualifier_*` |
| a real editable artifact | genuine OOXML writer with content types, relationships, styles and numbering | `build-docx-report.json`, `verification.json` (`format:*`, `text:*`) |
| honest status and limits | the audit always writes its `limitations`; the writer lists unsupported constructs; the preview states a missing renderer | `quantity-report.json.limitations`, `build-*-report.json.unsupported_constructs`, `preview-report.json.note` |
| reproducibility | plan, sections and sources are hash-bound and re-read | `plan_sha256`, `source_version_*`, `quote_source_version_*` |

Task-specific requirements:

- no performance claim exceeds the conditions the source reports it under
- readiness/maturity statements match what the material actually documents
- each application claim is marked as demonstrated, expected or untested
