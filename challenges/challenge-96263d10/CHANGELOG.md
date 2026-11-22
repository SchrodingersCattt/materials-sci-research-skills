# Changelog — 学术格式与模板适配

Channel: `challenge-96263d10`. Versioning is per candidate directory; the tree hash is recorded in
the session inventory so a submitted bundle can be identified exactly.

## v1 — 2026-11-16

- first published build of this candidate for this channel
- runtime is standard library only; no network call, no pip install, no Office suite
- added: reusable templates, reusable item set, check list, rubric map, gain protocol,
  innovation boundary

## v2 — 2026-11-22

- added: `linkage` — a per-caption, per-cross-reference, per-reference-entry audit of a manuscript
  or an adapted document, with `defects` carrying a `kind` and a `locator`, and `observations` for
  the layout conventions the audit cannot judge (caption on the other side of its object, reference
  list in another order)
- added: `linkage --renumber` — updates a caption number and every in-text reference that points at
  that caption in one pass, writes a new document, lists each change, and refuses (status
  `ambiguous`, no file written) when the document does not determine the answer
- added: `verify` checks `caption_inventory_preserved`, `cross_reference_resolution_preserved`,
  `reference_list_preserved`, `field_codes_preserved`; `specify` items `captions`,
  `cross_references`, `reference_list`, `template_apparatus`
- fixed: a template style that the style mapping targets is imported even when the manuscript
  already has a differently-named style with the same style *name*. Importing by name alone left the
  mapped style id undefined in the output, so the template's caption formatting was silently lost
  (`style_definitions_present` failed). Found on a manuscript the size of a real one, not on the
  five-row fixture.
- fixed: `verify` without `--spec` crashed (`template_path` was only bound inside the spec branch)
- added: `examples/linkage_case.py` and `tests/linkage_checks.py` — a realistic-size manuscript in a
  defective and a clean variant, used as the true-positive / true-negative control
- `run_case.py finish` runs the apparatus audit on an adapted DOCX and reports `linkage` with
  `defect_kinds`

## v1 — 2026-11-16

- first published build of this candidate for this channel
- runtime is standard library only; no network call, no pip install, no Office suite
- added: reusable templates, reusable item set, check list, rubric map, gain protocol,
  innovation boundary

## Maintenance policy

- extend the check list before adding dependencies
- every change reruns `tests/run_checks.py` and `tests/linkage_checks.py`; a change that cannot keep
  the negative paths failing is reverted
- a change to the runtime that was found on a realistic-size input is recorded here with the input
  that found it, because the five-row fixture does not exercise document order
- a failed reproduction is reported as a failed reproduction, not silently re-tested into a
  pass
