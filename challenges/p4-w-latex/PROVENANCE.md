# Provenance

Composed from the shared engine library for challenge `product-arena-07-865de7e4` (writing).

- `scripts/run_case.py`, `scripts/gain_check.py`, `scripts/contract_check.py`, `scripts/number_scan.py`
  — shared framework, identical across every composed package, so behaviour does not vary between
  challenges.
- `scripts/evidence_ledger.py` — the domain
  engine for this task shape.
- `tests/gain_cases/` — a synthetic source with one grounded control and three planted defects, used to
  prove the gain check rejects what it should.

Python 3.10+, standard library only. No network, no pip, no Office suite required.

Public work index: https://github.com/SchrodingersCattt/materials-sci-research-skills/tree/main/challenges/product-arena-07-865de7e4
