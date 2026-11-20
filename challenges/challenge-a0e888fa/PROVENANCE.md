# Provenance

Composed from the shared engine library for challenge `challenge-a0e888fa` (analysis).

Engines: data_profile.py.
Framework: `run_case.py`, `gain_check.py`, `contract_check.py`, `number_scan.py` — identical across
every composed package.

Python 3.10+, standard library only plus the declared toolchain (`scientific-python`, `SQLite`).
No network, no pip beyond what the sandbox provides.

## Domain basis

`visualize_data.py` is the `visualize-data` skill, MIT licensed, and its 18 QA capabilities map onto
this rubric's own list (whitespace, clipping, boundary, labels, geometry, print scale, semantic colour,
cross-panel consistency, quantitative disclosure, integrity, output discipline, five-problem review,
strict gate). Its mandatory manifest-to-delivery workflow is the chain this track describes.

`data_profile.py` and `sql_audit.py` are new construction. No data-profiling, statistics or SQL-audit
library existed in any available source, and the quality-report requirement — that the report's numbers
come from the same computation as the result table — is the failure the brief names.

Public work index: https://github.com/SchrodingersCattt/materials-sci-research-skills/tree/main/challenges/challenge-a0e888fa
