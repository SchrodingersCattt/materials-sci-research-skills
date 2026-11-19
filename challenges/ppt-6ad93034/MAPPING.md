# Mapping: case requirement → mechanism → verification

Task: 学术 PPT 生成与编辑.

| Requirement | Mechanism | Evidence |
|---|---|---|
| the supplied template is really used | `inspect` reads master/layouts/placeholders/theme; `merge` writes into the layout's own placeholders and clones layout-shaped pages | `deck.json`; `merge-report.json` (`template_parts_unchanged`, `changed_parts`) |
| master/layout/placeholder inheritance is preserved | masters, layouts and theme are copied byte-for-byte; every slide points at a real layout | `slide-check.json`: `master_kept`, `theme_kept`, `template_bytes_kept`, `placeholder_inheritance` |
| page content is traceable to the source | each planned text entry may carry a `source_locator`; the checker re-reads the produced slides | `merge-report.json` (`operations[].filled[].source_locator`); `slide-check.json` `declared_content_present` |
| layout constraints are checked | frame geometry is read from the package and the required height is estimated with a declared formula | `slide-check.json`: `no_estimated_overflow`, `overflow_estimates[]` |
| deliverable and reproducible | a normal PPTX validated by an independent tool, plus a real rendered preview whose text is read back | `tests/validate_package.py`; `preview-report.json` (`slides`, `rendered_text`) |
| honest limits | a missing placeholder, a missing clone source, an estimated overflow and a missing renderer are named | `merge-report.json` (`missing_placeholders`, `status`); `slide-check.json`; `preview-report.json.note` |

Task-specific requirements:

- the requested mode (generate vs edit) is identified and followed
- for an edit: untouched slides are byte-identical to the supplied deck
- new pages inherit a real layout and placeholder structure
- estimated overflow and any missing placeholder are reported, not hidden
