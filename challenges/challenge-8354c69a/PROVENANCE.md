# Provenance

Composed from the shared engine library for challenge `challenge-8354c69a` (experiment).

Engines: `protocol_audit.py` (protocol model, feasibility gate, parameter provenance, comparison
matrix, anomaly detection, cost roll-up), `quantity_audit.py` (numeric traceability).
Framework: `run_case.py`, `gain_check.py`, `contract_check.py`, `number_scan.py` — identical across
every composed package.

Python 3.10+, standard library only. No network, no pip.

## Domain basis

The rule that governs this track — an unstated requirement is `not_stated`, never satisfied — and the
feasibility state machine (`VERIFIED_EXECUTABLE`, hold and reject states, capability-versus-requirement
comparison) are adapted from an internal analytical-chemistry benchmark's feasibility gate. The
protocol parameter vocabulary (unit, range, instrument, measurement method, control kinds, parameter
basis) follows the stage tables of 27 report-derived analytical protocols covering atomic
spectroscopy, chromatography, electrochemistry, thermal analysis, diffraction and materials
characterisation. No third-party text is reproduced; the parameter and control conventions are
re-expressed.

Cost and time modelling are **new construction**: no price list, machine-hour rate, labour rate, lead
time table or budget template existed in any available source. Every rate must be supplied by the case
or by the operator, and a missing rate is reported rather than assumed.

Public work index: https://github.com/SchrodingersCattt/materials-sci-research-skills/tree/main/challenges/challenge-8354c69a
