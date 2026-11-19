# exact-formula-derivation

A skill for the formula/math task: the supplied expression and its declared values are evaluated
**exactly**, with the declared domains and bounds checked and a re-runnable step ledger as the
deliverable.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/formula_check.py` | the runtime: `check` (evaluate exactly) and `verify` (re-derive) |
| `MAPPING.md` | case requirement → mechanism → verification |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | the synthetic formula spec used by the self-test |
| `tests/run_checks.py` | positive path plus four negative paths |

## Requirements

Python 3.10+ and the standard library only. No network, no `pip install`, no sympy, no numpy.

## Use

```
python scripts/formula_check.py check  --spec work/formula.json --outdir work/formula
python scripts/formula_check.py verify --spec work/formula.json --outdir work/formula
```

`check` writes `formula-report.json` with one entry per step: the readable substitution, the exact
Python expression actually evaluated, the exact value as `numerator/denominator`, the display
rounding (separate from the exact value), the unit carried verbatim, and a range note that states
either the material's own range or an explicit "the material states no range". Exit code `2` means
at least one step failed; `verify` writes `formula-verification.json`.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

Positive path: a rational momentum balance evaluated exactly to `11/6` with an explicit `1.8333`
display, a decimal volume inside the range the fixture states, and a rate whose denominator is a
non-zero difference with a declared expected value. Negative paths: a zero denominator, a domain
violation, a symbol the material never reports, and a wrong expected value must each be reported.

## Scope and limits

- Supported operations: `+ - * / ^` and `abs/min/max` on declared values. No symbolic algebra, no
  solving for a symbol, no unit algebra, no calculus.
- Exactness is enforced: everything becomes a `Fraction` (decimals through their exact decimal
  value), and an evaluation that would fall back to floating point is refused instead of reported
  as a checked value.
- Every domain rule must be a numeric bound (`>=`, `<=`, `>`, `<`, `!=`, `==`); a symbolic
  constraint is reported as unsupported rather than assumed.
- The checker reports the range the material states, and states explicitly when the material
  states none. It never invents or tightens one.
- Not an official score and not proof that the expression is the right model for the science.

## Maintenance

One standard-library script. Extend the operator set and the status vocabulary, not the dependency
list, and keep `tests/run_checks.py` green — including its four negative paths.
