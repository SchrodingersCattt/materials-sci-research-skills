# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for the slide tasks
(academic PPT generation, template adaptation, paper→deck conversion). It replaces an earlier
candidate whose primary path required a pinned `doc-forge` installation plus an Office suite inside
the evaluation container; this version is standard-library only, so nothing in the deliverable
depends on an unverifiable runtime.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`zipfile`, `xml.etree`, `json`, `hashlib`, `subprocess`, `shutil`) | the entire runtime |
| the OOXML presentationML part layout | read and patched directly; no python-pptx |
| LibreOffice + Poppler (optional) | PDF/PNG preview and rendered-text check |

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — 4 placeholders filled, 1 slide added from the layout, template parts unchanged, 8/8 checks pass |
| `tests/validate_package.py` (independent of the editor) | accepts both the fixture deck and the edited deck: every XML part well-formed, every relationship target present, every part covered by a content type, every slide pointing at a layout |
| LibreOffice render of the edited deck | real PDF + 3 slide PNGs; extracted PDF text contains the filled titles and bullets, confirming the content survived the render |
| negative paths | a missing target slide, a missing placeholder and an overflowing body are each reported by name |

Failures found and fixed while building this (kept because they are the real risks):

1. Re-serialising `[Content_Types].xml` with ElementTree rewrote the default namespace as a `ct:`
   prefix, which the consumer rejected — parts are now patched textually so declarations survive.
2. Setting `xmlns:*` attributes on a tree that ElementTree also writes produced duplicate
   attributes — declarations the tree does not use are now injected textually after serialisation.
3. Passing `-env:UserInstallation=...` to `soffice` on this platform crashed the converter; the
   renderer call now uses a clean invocation with one retry instead.

## Boundaries

- Fills placeholders and clones layout-shaped slides. Images, charts, SmartArt, transitions and
  notes are out of scope unless a template slide already carries them.
- The overflow figure is an estimate; the rendered preview is the visual check.
- The checks prove template fidelity, declared-content presence and package validity. They are not
  an official score and not a judgement about the deck's scientific storyline.
- Resource budget observed: 8 UTF-8 text files, largest 35 KB, 96 KB total — inside the 50-file /
  500 KB-per-file / 2 MB-total skill resource limits.
