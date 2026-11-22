# Ecosystem contribution — reading engine (question-shaped and field-shaped cases)

The organizer grades documentation completeness, reuse by others, and shareable experience. This file
is the map; the inventory below is generated from the actual directory contents. The engine is shared
by the reading channels, so it is described channel-neutrally.

## Documentation completeness

| Asked for | Where |
|---|---|
| usage instructions | `README.md` (Use), `SKILL.md` (Workflow) |
| dependencies and configuration | `README.md` (Requirements), `PROVENANCE.md` |
| examples | `examples/synthetic_case.py`, `tests/cases/`, `tests/qa_checks.py` |
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

## File inventory (23 files, 98590 bytes)

| Path | Bytes | Role |
|---|---|---|
| `CHANGELOG.md` | 798 | documentation |
| `CHECKLIST.md` | 3970 | documentation |
| `ECOSYSTEM.md` | 2127 | documentation |
| `examples/synthetic_case.py` | 6298 | interface fixture |
| `GAIN.md` | 1914 | documentation |
| `INNOVATION.md` | 2296 | documentation |
| `MAPPING.md` | 2413 | documentation |
| `PROVENANCE.md` | 2082 | documentation |
| `README.md` | 2896 | documentation |
| `RUBRIC.md` | 22539 | documentation |
| `scripts/contract_check.py` | 18506 | runtime script |
| `scripts/reading_contract.py` | 17769 | runtime script |
| `SKILL.md` | 7494 | instruction the evaluator agent reads first |
| `templates/change-log-template.csv` | 87 | reusable template |
| `templates/deliverable-plan-template.json` | 467 | reusable template |
| `templates/figure-table-pointer-template.csv` | 66 | reusable template |
| `templates/glossary-template.csv` | 70 | reusable template |
| `templates/reference-map-template.csv` | 95 | reusable template |
| `tests/cases/item-01.json` | 796 | self-test and negative paths |
| `tests/cases/item-02.json` | 805 | self-test and negative paths |
| `tests/cases/item-03.json` | 806 | self-test and negative paths |
| `tests/cases/README.md` | 449 | self-test and negative paths |
| `tests/run_checks.py` | 3847 | self-test and negative paths |

Limits observed: at most 50 text files, 500 KB per file, 2 MB in total, no symlinks.
