# Provenance

Composed from the shared engine library for challenge `challenge-5c918ff0` (search).

Engines: `retrieval_audit.py` (strategy, screening record, stage reconciliation, coverage bound,
appraisal with weights, cross-language synonym sets), `file_inventory.py` (corpus discovery, content-hash
de-duplication, version chains).
Framework: `run_case.py`, `gain_check.py`, `contract_check.py`, `number_scan.py` — identical across
every composed package.

Python 3.10+, standard library only. **No network**: every source is supplied in the case, so the task is
retrieval discipline over a supplied corpus rather than database access.

Every record in this skill is made mechanically rather than asserted: an inclusion names the criterion
that produced it, the stage counts reconcile against the declared record count, a criterion that cannot
be adjudicated is rejected, and the conclusion carries an explicit bound.

Public work index: https://github.com/SchrodingersCattt/materials-sci-research-skills/tree/main/challenges/challenge-5c918ff0
