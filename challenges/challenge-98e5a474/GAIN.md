# Gain and its verification — 科研示意图生成与编辑

Channel: `challenge-98e5a474`.

## What the platform compares

The statement fixes how use gain is measured: the same three organizer cases are run by the
same agent with and without this skill, three repetitions per condition, and the platform
computes the comparison. This skill therefore aims at behaviour that survives repetition:

- the same command sequence works for every case, so the second and third run cost no
  extra reasoning about the procedure;
- the audit is rerun after every edit, so a regression is detected in the run that caused
  it rather than by a later human reading pass;
- artifacts are rebuilt from the source Markdown on every run, so the deliverable and the
  verified text cannot drift apart.

## Measurements actually taken here

- Self-test on the shipped fixture: **pass**, 33 checks, 0 failures.
- Injected-defect detection: the negative paths in `tests/run_checks.py` are built
  from deliberately broken inputs; the reported count is the number of those inputs
  the checker refused, and the fixture script rebuilds them on every run.

## Reproduce

```
python examples/synthetic_case.py --outdir work/fixture
python tests/run_checks.py --workdir work/lab
```

Expect the same verdict and the same check count as above; the fixture is deterministic and
needs no network.

## Efficiency claim, stated narrowly

The claim is the number of manual passes, not a wall-clock saving: the workflow turns
"draft → human reread → fix numbers → re-type into the container format → re-read" into
"draft → one audit command → one build command → one verify command". The audit returns exit
code 2 with the failing check id, so the repair is a lookup rather than a search. Where a
renderer is missing, the run reports the missing renderer instead of adding a manual step.
