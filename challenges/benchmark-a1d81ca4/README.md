# benchmark-case-authoring

A skill for the benchmark tasks: a case set becomes a runnable evaluation artefact — material that
resolves, expected answers that are stated, anchors with weights, and a score computed by a declared
rule.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/benchmark_build.py` | the runtime: `validate`, `score`, `verify` |
| `MAPPING.md` | case requirement → mechanism → verification |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | a two-case fixture spec, reference answers and weak answers |
| `tests/run_checks.py` | positive path plus four negative paths |

## Requirements

Python 3.10+ and the standard library only. No network, no `pip install`, no model call, no grading
service.

## Use

```
python scripts/benchmark_build.py validate --spec work/benchmark.json --outdir work/benchmark
python scripts/benchmark_build.py score    --spec work/benchmark.json --answers work/answers.json --outdir work/scoring
python scripts/benchmark_build.py verify   --spec work/benchmark.json --outdir work/benchmark
```

Exit codes: `0` valid/scored, `2` the set is not runnable (the report lists the problems), `3`
verification failed. `validate` writes `benchmark-report.json`; `score` writes `scoring-report.json`
with per-case results, matched anchors, missed required anchors and the total; `verify` writes
`benchmark-verification.json`.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

Positive path: the set validates, the reference answers score `normalised_total = 1.0`, the weak
answers score strictly lower with both penalties matched. Negative paths: a missing required field,
unresolvable material, anchors that do not sum to the declared maximum, and a duplicate case id must
each fail validation.

## Scope and limits

- The scorer matches normalised substrings of the anchors against a JSON answer object. It is
  deliberately simple and inspectable: a case needing semantic judgement must say so, and its anchors
  must be written so that a substring match is the right test.
- The score is reproducible for **this** rubric. It is not a platform score, and it is not a
  substitute for expert review.
- The validator checks structure, resolvability and weight arithmetic. It cannot certify that the
  expected answers are scientifically correct — that judgement stays with the author and the reviewer.
- Not an official score, and no model is called anywhere in the runtime.

## Maintenance

One standard-library script. Extend the anchor kinds (for example an ordered-sequence anchor) and the
validation rules, not the dependency list, and keep `tests/run_checks.py` green — including its four
negative paths.
