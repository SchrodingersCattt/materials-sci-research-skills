# Provenance

## Origin

Authored in the session that produced this directory (2026-11-15, Asia/Shanghai) as a
replacement for the earlier template-adaptation candidate whose primary path depended on a
pinned `doc-forge` installation and an Office suite being present in the evaluation
container. This version performs the same method with the Python standard library only, so
the deliverable no longer depends on an unverifiable runtime assumption.

## Upstream relationship

| Upstream | Use here |
|---|---|
| [doc-forge](https://github.com/SchrodingersCattt/doc-forge), MIT, commit `1fa02b08aea33debb3cc9fb1b5af138dd7e9b006`, distribution `docforge` 0.1.0 | its `restyle` method (import template style definitions into the source package, re-point paragraphs, keep unrelated parts byte-identical) is the model this skill implements independently. No doc-forge source is vendored, imported or required. |
| Python standard library (`zipfile`, `xml.etree`, `json`, `hashlib`, `subprocess`, `shutil`) | the entire runtime |
| LibreOffice + Poppler (optional) | PDF/PNG preview and font report when present |

`adapt_template.py` is not the upstream package and does not claim upstream behaviour,
audit semantics or compatibility.

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — spec fully mapped, text stream preserved, 26/26 checks pass |
| `tests/linkage_checks.py` on `examples/linkage_case.py` (local, Python 3.12) | pass — the defective variant is reported `needs_work` with all four planted defect kinds named by locator; the clean variant is reported `consistent` with no defect and no observation; `--renumber` leaves no caption out of sequence and carries the in-text references with it |
| same self-test inside `python:3.11-slim` with `--network none` | pass — identical results with no network and no Office suite |
| non-DOCX template refusal path | exit 2 with `reason` recorded in `apply-report.json` |
| realistic manuscript (~40 paragraphs, 3 figures, 2 tables, 12 references) through specify → apply → verify | 27/27 checks pass; this input is what exposed the style-import defect fixed in v2 (a mapping target whose style *name* the manuscript reused under another id was skipped, leaving the output with an undefined style) |
| real render of the adapted fixture (`soffice --convert-to pdf` + `pdftoppm`) | page-1 PNG inspected; template heading, caption and table styling visibly applied; A4 page from the template |

All fixture values are invented for interface testing. No formal case, hidden material or
official score was used to build or validate this skill.

## Boundaries

- The skill proves geometry, style application, content preservation, package integrity and the
  caption/cross-reference/reference-list apparatus. It does not prove typographic quality,
  scientific meaning or any official score.
- Prose-only or PDF templates have no style definitions to import; the stated rules are
  applied where the format allows and the rest is reported as unchecked.
- Caption numbers and the in-text references that point at them are audited and can be renumbered
  together. TOC fields, header/footer boilerplate and journal front matter are preserved, not
  regenerated: a case that requires the template's own headers, front matter or a rebuilt table of
  contents needs an explicit, recorded decision by the agent. The layout conventions the audit
  cannot judge (which side of the object a caption belongs on, whether a reference list is in
  citation order) are reported as observations, not as defects.
- Resource budget observed: 37 UTF-8 text files, largest 83 KB, 254 KB total — inside the
  50-file / 500 KB-per-file / 2 MB-total skill resource limits.
