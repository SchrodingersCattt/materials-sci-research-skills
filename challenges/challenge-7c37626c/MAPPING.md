# Mapping: case requirement → mechanism → verification

Task: formula parsing and mathematical reasoning over supplied material. No official scoring claim
is made here.

| Requirement | Mechanism | Evidence |
|---|---|---|
| Read the expression and its symbols from the material, not from memory | the spec stores the expression verbatim plus one entry per symbol with its value and source locator; an expression naming a symbol with no declared value is refused | report `steps[].problems` ("uses undeclared variable(s)"), `steps[].variable_sources` |
| The checked value must be exact | every declared literal becomes a `Fraction` (decimals via their exact decimal value), the substitution uses `Fraction(n, d)` so Python cannot fall back to float, and an evaluation that produces a float is refused | report `steps[].exact` (`11/6`), `steps[].assumptions.exact_python_expression`; refusal message "lost exactness" |
| Assumptions and domains must be explicit | declared domain rules are evaluated against the declared values before any substitution; an unsupported (non-numeric) rule is reported rather than assumed | report `steps[].status == "domain_violation"` with the violated rule |
| A denominator that can be zero must not be resolved silently | a declared zero in a denominator position is caught symbolically, and a `ZeroDivisionError` during evaluation is mapped to the same status | report `steps[].status == "unresolved_denominator"` |
| Bounds only where the material states them | `declared_range` is carried through with its own source locator; a step without one records "the material states no range for this quantity" | report `steps[].declared_range`, `steps[].range_note` |
| Precision must not be confused with accuracy | the display value is produced by an explicit `ROUND_HALF_EVEN` at the declared number of places and is labelled as the display, while the exact value remains the checked one | report `steps[].display`, `steps[].display_note` |
| A reader can re-run it | `verify` rebuilds the report from the spec, records the spec hash, and checks that every step carries a range note, an exact value and a status | `formula-verification.json` (`spec_hash_recorded`, `no_undeclared_range`, `exact_values_recorded`, `steps_reported`) |
| Honest limits | unsupported operators, non-integer exponents, symbolic constraints, unassigned symbols and unit algebra are named as limitations rather than approximated | report `limitations`, `steps[].status == "error"`, `unit_note` |
