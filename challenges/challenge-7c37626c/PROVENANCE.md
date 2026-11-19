# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for the formula
parsing and mathematical reasoning task, as a standard-library replacement for an earlier candidate
whose primary path required a pinned `doc-forge` installation. The arithmetic here is exact by
construction, not by convention.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`fractions`, `decimal`, `re`, `json`, `hashlib`) | the entire runtime |
| no sympy, no numpy, no network | deliberately not used |

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — 7 checks, 0 failures |
| exactness | the rational momentum balance reports `exact = 11/6` and `display = 1.8333`; a float result is refused with "lost exactness" |
| assumptions | a declared `m1 > 5` against a declared `m1 = 2` reports `domain_violation`; a denominator that evaluates to zero reports `unresolved_denominator`; a symbol the fixture never reports reports `error` naming the symbol |
| wrong expectations | a declared `expect` that disagrees with the exact value reports `mismatch` rather than being ignored |
| reproducibility | `verify` rebuilds the report from the spec, records the spec hash and confirms every step carries a status, an exact value and a range note |

Failures found and fixed while building this (kept because they are the real risks):

1. Mixing `Fraction` and `Decimal` made Python fall back to binary floats — every declared literal
   now becomes a `Fraction` and the substitution emits `Fraction(n, d)`.
2. Substituting a bare integer numerator turned `45 / (60 - 30)` into float division — fixed by the
   same change.
3. A denominator that becomes zero only after substitution escaped the symbolic scan — the
   `ZeroDivisionError` is now mapped to the same explicit status.

## Boundaries

- Arithmetic on declared values only. No symbolic algebra, no solving, no calculus, no unit algebra.
- A symbolic domain constraint (for example `x > y`) is reported as unsupported, not assumed.
- The report states the material's own range or an explicit none; it never invents a bound.
- Not an official score and not proof that the expression is the right model for the science.
- Resource budget observed: 6 UTF-8 text files, largest 22 KB, 42 KB total — inside the 50-file /
  500 KB-per-file / 2 MB-total skill resource limits.
