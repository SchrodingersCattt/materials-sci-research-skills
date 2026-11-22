# Ecosystem contribution — 学术格式与模板适配

Channel: `challenge-96263d10`. The organizer grades documentation completeness, reuse by others,
and shareable experience. This file is the map; the inventory below is generated from the
actual directory contents.

## Documentation completeness

| Asked for | Where |
|---|---|
| usage instructions | `README.md` (Use), `SKILL.md` (Workflow) |
| dependencies and configuration | `README.md` (Requirements), `PROVENANCE.md` |
| examples | `examples/synthetic_case.py`, `examples/linkage_case.py`, `tests/cases/` |
| applicable scope and limits | `SKILL.md` (Scope), `README.md` (Scope and limits) |
| length and size limits | `README.md`, and the run's own budget note in `SKILL.md` |
| known failure modes | `SKILL.md` (Failure handling), `CHECKLIST.md` |
| maintenance information | `CHANGELOG.md`, `README.md` (Maintenance) |

## Reusable resources

Anyone can take these without this candidate's context: the runtime scripts (standard
library only), the templates in `templates/`, the item set in `tests/cases/`, the check list
in `CHECKLIST.md`, and the requirement-to-evidence table in `MAPPING.md`.

## Sharing value

The transferable part is the pattern, not the prose: read the case's own contract, declare
every number against a source row, build a real container, re-read it, and report the limits.
It is written down here so another author can apply it to a neighbouring task.

﻿## File inventory (37 files, 259676 bytes)

| Path | Bytes | Role |
|---|---|---|
| `CHANGELOG.md` | 2978 | documentation |
| `CHECKLIST.md` | 4309 | documentation |
| `ECOSYSTEM.md` | 2932 | documentation |
| `examples/linkage_case.py` | 12769 | interface fixture: realistic-size manuscript, defective and clean |
| `examples/synthetic_case.py` | 9326 | interface fixture: small template/manuscript pair |
| `GAIN-EVIDENCE.md` | 4196 | documentation |
| `GAIN.md` | 1912 | documentation |
| `INNOVATION.md` | 3840 | documentation |
| `MAPPING.md` | 4438 | documentation |
| `PROVENANCE.md` | 2792 | documentation |
| `README.md` | 5228 | documentation |
| `RUBRIC.md` | 7036 | documentation |
| `scripts/adapt_template.py` | 84698 | runtime script: the adaptation pipeline and the apparatus audit |
| `scripts/contract_check.py` | 18506 | runtime script: output-contract extraction and conformance |
| `scripts/gain_check.py` | 14888 | runtime script: gain and grounding measurement |
| `scripts/number_scan.py` | 11902 | runtime script: number traceability scan |
| `scripts/run_case.py` | 18270 | runtime script: the mechanical half of a case in two commands |
| `SKILL.md` | 21625 | instruction the evaluator agent reads first |
| `templates/change-log-template.csv` | 87 | reusable template |
| `templates/deliverable-plan-template.json` | 467 | reusable template |
| `templates/figure-table-pointer-template.csv` | 66 | reusable template |
| `templates/glossary-template.csv` | 70 | reusable template |
| `templates/reference-map-template.csv` | 95 | reusable template |
| `templates/section-evidence-map.csv` | 98 | reusable template |
| `tests/cases/item-01.json` | 796 | reusable interface item |
| `tests/cases/item-02.json` | 805 | reusable interface item |
| `tests/cases/item-03.json` | 806 | reusable interface item |
| `tests/cases/README.md` | 449 | reusable interface item |
| `tests/gain_cases/answer-fabricated.json` | 181 | documentation |
| `tests/gain_cases/answer-grounded.json` | 958 | documentation |
| `tests/gain_cases/answer-hedge-stripped.json` | 100 | documentation |
| `tests/gain_cases/answer-off-topic.json` | 90 | documentation |
| `tests/gain_cases/material/material.md` | 572 | documentation |
| `tests/gain_cases/README.md` | 465 | documentation |
| `tests/gain_checks.py` | 5074 | self-test: gain controls, including a fabricated number |
| `tests/linkage_checks.py` | 12566 | self-test: true-positive/true-negative control for the apparatus audit |
| `tests/run_checks.py` | 4286 | self-test and negative paths |

Limits observed: at most 50 text files, 500 KB per file, 2 MB in total, no symlinks.
