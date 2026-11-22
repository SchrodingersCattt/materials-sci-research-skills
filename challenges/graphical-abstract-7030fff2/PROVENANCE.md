# Provenance

Composed from the shared engine library for challenge `graphical-abstract-7030fff2` (graphics).

Engines: `make_figure.py` (chart and diagram build: editable SVG, PNG and PDF export, raster
inspection, conformance verification), `edit_svg.py` (source-preserving, hash-pinned edit of a supplied
SVG), `route_svg.py` (a normalized box-and-arrow route from an explicitly authored plan).
Framework: `run_case.py`, `gain_check.py`, `contract_check.py`, `number_scan.py` — identical across every
composed package.

Python 3.10+, standard library only. **No network.** The material supplies the sources, the data and any
figure or template to be edited.

Every claim in the deliverable is made mechanically rather than asserted: each drawn element carries the
locator it was read at, the export is inspected rather than promised, and a supplied figure is edited
under a record that names what changed.

Public work index: https://github.com/SchrodingersCattt/materials-sci-research-skills/tree/main/challenges/graphical-abstract-7030fff2
