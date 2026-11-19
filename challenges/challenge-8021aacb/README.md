# source-located-structural-editing

A skill for the structure/logic-optimisation topic: a manuscript gets a rule-based structural
diagnosis located to paragraph and sentence, an executable edit list, and a restructured
document that provably keeps everything it did not intend to change.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/structure_audit.py` | the runtime: `inspect`, `outline`, `claims`, `diagnose`, `plan`, `apply`, `verify` |
| `MAPPING.md` | requirement direction → mechanism → evidence |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_manuscript.py` | builds the synthetic manuscript used by the self-test |
| `tests/run_checks.py` | builds the fixture, runs the pipeline, asserts the contract |

## Requirements

Python 3.10+ and the standard library only (`zipfile`, `xml.etree`, `re`, `json`, `hashlib`).
No network, no `pip install`, no doc-forge, no Office suite is needed for any step.

## Use

```
python scripts/structure_audit.py inspect  /input/manuscript.docx --out work/inspect.json
python scripts/structure_audit.py outline  --doc /input/manuscript.docx --out work/outline.json
python scripts/structure_audit.py claims   --doc /input/manuscript.docx --out work/claims.json
python scripts/structure_audit.py diagnose --doc /input/manuscript.docx --out work/findings.json
python scripts/structure_audit.py plan     --doc /input/manuscript.docx --out work/plan.json
python scripts/structure_audit.py apply    --doc /input/manuscript.docx --plan work/plan.json --outdir work/edit
python scripts/structure_audit.py verify   --doc /input/manuscript.docx --output work/edit/restructured.docx --outdir work/edit
```

Exit codes: `0` success, `2` refused (read `reason`), `3` verification found failures.

## Self-test

```
python examples/synthetic_manuscript.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

The fixture is built to contain a heading-level jump, a duplicated paragraph, a causal claim
with no statistic or citation, an absolute claim, an unsourced quantity, interpretation inside
the results section and a missing objective. The self-test asserts every one of those rules
fires, that exactly one action is executable, that applying it removes exactly the duplicated
paragraph, that verification passes, and that a second plan run finds nothing left to do.

## Scope and limits

- Findings are rule-based text analysis over the inspected range: they locate problems, they
  do not decide them. Every finding carries `needs_human_decision` and the rule that fired.
- Only duplicate-paragraph deletion is executed automatically, because it is the one edit that
  provably preserves every other sentence. Moves, merges, splits and wording changes stay as
  located instructions — a structural change to an author's argument is theirs to accept.
- Non-DOCX input: analysis still runs, but `apply` refuses and the plan remains instructions.
- The verification proves preservation and the applied deletions. It does not judge whether a
  structural suggestion is scientifically correct, and it is not an official score.

## Maintenance

Single-file runtime, no third-party imports. Extend the rule list and the check list, not the
dependency list, and keep `tests/run_checks.py` green — including its expectation that exactly
one fixture action is executable.
