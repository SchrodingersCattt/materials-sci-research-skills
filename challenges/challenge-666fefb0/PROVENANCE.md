# Provenance

Composed from the shared engine library for challenge `challenge-666fefb0` (library).

Engines: file_inventory.py, reading_contract.py.
Framework: `run_case.py`, `gain_check.py`, `contract_check.py`, `number_scan.py` — identical across
every composed package, so behaviour does not vary between challenges.

Python 3.10+, standard library only. No network, no pip, no Office suite.

The reorganisation path is reversible by construction: `plan` writes nothing, `apply` journals every
rename, and `rollback` reverses the journal.

Public work index: https://github.com/SchrodingersCattt/materials-sci-research-skills/tree/main/challenges/challenge-666fefb0
