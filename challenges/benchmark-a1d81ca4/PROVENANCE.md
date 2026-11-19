# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for the two benchmark
tasks (literature-reading benchmark, academic-writing benchmark), as a standard-library candidate
that does not depend on a pinned `doc-forge` installation. The delivered artefact is the case set and
its validation/scoring reports; the platform's own scoring stays the platform's business.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`json`, `hashlib`, `re`, `pathlib`) | the entire runtime |
| no model call, no grading service, no network | deliberately not used |

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — 7 checks, 0 failures |
| validation | the two-case fixture validates; a case missing `instruction`, a case referencing missing material, anchors that do not sum to `max_points`, and a duplicate case id each fail validation |
| scoring | the reference answers reach `normalised_total = 1.0`; the weak answers score strictly lower with both penalties matched (overstated significance and asserted causation) |
| reproducibility | `verify` re-validates from the spec and records the spec hash; `score` records both the spec and the answer hash |
| weight arithmetic | a mismatch between earnable anchor weights and `max_points` is reported during validation, before any scoring run |

## Boundaries

- Anchors are matched by normalised substring against a JSON answer object. A case that needs
  semantic judgement must declare that in its instruction and word its anchors so a substring test is
  the right one; the runtime does not call a model.
- The score is reproducible for the declared rubric only. It is not a platform score and not a
  substitute for expert review.
- Structure, resolvability and weight arithmetic are validated; scientific correctness of the
  expected answers is the author's and reviewer's responsibility and is stated as such.
- Resource budget observed: 6 UTF-8 text files, largest 21 KB, 40 KB total — inside the 50-file /
  500 KB-per-file / 2 MB-total skill resource limits.
