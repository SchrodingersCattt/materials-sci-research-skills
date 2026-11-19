# Ecosystem contribution — 写作15｜开题报告与研究计划书

Channel: `challenge-142d91a2`. The organizer grades documentation completeness, reuse by others,
and shareable experience. This file is the map; the inventory below is generated from the
actual directory contents.

## Documentation completeness

| Asked for | Where |
|---|---|
| usage instructions | `README.md` (Use), `SKILL.md` (Workflow) |
| dependencies and configuration | `README.md` (Requirements), `PROVENANCE.md` |
| examples | `examples/synthetic_case.py`, `tests/cases/` |
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

## File inventory (24 files, 125580 bytes)

| Path | Bytes | Role |
|---|---|---|
| `CHANGELOG.md` | 810 | documentation |
| `CHECKLIST.md` | 4003 | documentation |
| `ECOSYSTEM.md` | 2187 | documentation |
| `examples/synthetic_case.py` | 5096 | interface fixture |
| `GAIN.md` | 1928 | documentation |
| `INNOVATION.md` | 2383 | documentation |
| `MAPPING.md` | 1977 | documentation |
| `PROVENANCE.md` | 1648 | documentation |
| `README.md` | 2432 | documentation |
| `RUBRIC.md` | 5186 | documentation |
| `scripts/contract_check.py` | 18506 | runtime script |
| `scripts/deliver.py` | 49989 | runtime script |
| `scripts/quantity_audit.py` | 12239 | runtime script |
| `SKILL.md` | 7720 | instruction the evaluator agent reads first |
| `templates/change-log-template.csv` | 87 | reusable template |
| `templates/deliverable-plan-template.json` | 467 | reusable template |
| `templates/figure-table-pointer-template.csv` | 66 | reusable template |
| `templates/glossary-template.csv` | 70 | reusable template |
| `templates/reference-map-template.csv` | 95 | reusable template |
| `tests/cases/item-01.json` | 796 | self-test and negative paths |
| `tests/cases/item-02.json` | 805 | self-test and negative paths |
| `tests/cases/item-03.json` | 806 | self-test and negative paths |
| `tests/cases/README.md` | 449 | self-test and negative paths |
| `tests/run_checks.py` | 5835 | self-test and negative paths |

Limits observed: at most 50 text files, 500 KB per file, 2 MB in total, no symlinks.
