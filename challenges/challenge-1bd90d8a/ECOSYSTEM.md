# Ecosystem contribution — 科研数据图表生成与编辑

Channel: `challenge-1bd90d8a`. The organizer grades documentation completeness, reuse by others,
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

## File inventory (23 files, 118386 bytes)

| Path | Bytes | Role |
|---|---|---|
| `CHANGELOG.md` | 802 | documentation |
| `CHECKLIST.md` | 4452 | documentation |
| `ECOSYSTEM.md` | 2125 | documentation |
| `examples/synthetic_case.py` | 2696 | interface fixture |
| `GAIN.md` | 1918 | documentation |
| `INNOVATION.md` | 2307 | documentation |
| `MAPPING.md` | 2361 | documentation |
| `PROVENANCE.md` | 2582 | documentation |
| `README.md` | 3192 | documentation |
| `RUBRIC.md` | 5776 | documentation |
| `scripts/contract_check.py` | 18506 | runtime script |
| `scripts/make_figure.py` | 53035 | runtime script |
| `SKILL.md` | 7804 | instruction the evaluator agent reads first |
| `templates/change-log-template.csv` | 87 | reusable template |
| `templates/deliverable-plan-template.json` | 467 | reusable template |
| `templates/figure-table-pointer-template.csv` | 66 | reusable template |
| `templates/glossary-template.csv` | 70 | reusable template |
| `templates/reference-map-template.csv` | 95 | reusable template |
| `tests/cases/item-01.json` | 796 | self-test and negative paths |
| `tests/cases/item-02.json` | 805 | self-test and negative paths |
| `tests/cases/item-03.json` | 806 | self-test and negative paths |
| `tests/cases/README.md` | 449 | self-test and negative paths |
| `tests/run_checks.py` | 7189 | self-test and negative paths |

Limits observed: at most 50 text files, 500 KB per file, 2 MB in total, no symlinks.
