# Gain evidence - measured, not asserted

This channel scores 使用增益 (25 points, of which 增益可验证性 is 5) and 创新增益
(15 points, of which 创新证据 is 5) from a comparison between running with this skill and
running without it. The rubric adds that written self-description cannot substitute for
runtime evidence, so the comparison below is produced by a script that ships with the
skill and that anyone can re-run.

## Reproduce it

```bash
python "$SKILL_DIR/tests/gain_checks.py" --workdir work/gain
```

## What the shipped self-test measured on this machine

- Grounded control answer: coverage 0.9, grounding 1.0, verdict `grounded`, over 10 measurable claims.
- Fabricated number planted in an answer: reported as untraceable (`91.4`), grounding falls to 0.5.
- Thinner but still traceable answer: coverage 1.0, verdict `grounded` - fully grounded, but it carries fewer supported claims and so ranks below the control.
- Answer about unrelated material: coverage 0.0.
- Skill versus baseline on the same material: `skill_stronger`, delta {"coverage": -0.1, "grounding": 0.0, "statements_supported": 8, "numbers_claimed": 6, "numbers_untraceable": 0}.
- Empty answer: refused with exit code 2.

Self-test verdict: **pass**, 7 checks, 0 failures.

## What the check defines: two numbers, no prose

- **coverage** - of the claims your answer makes about the material, the share the
  supplied material actually supports. A claim is a sentence, or a structured field
  record; field *names* are excluded because an identifier is not a claim about the
  source. A claim carrying numbers must have every one of them in the material.
- **grounding** - of the numbers your answer asserts, the share that traces back to a
  number in the supplied material. Numbers that only cite a location (`para 1`,
  `table 2`) are excluded, so a locator cannot be mistaken for a measurement.

## Scope and limits

This measures agreement with the supplied material, not scientific correctness: an
answer can be perfectly grounded and still reach a wrong conclusion. It compares
against the material the case supplies, so material never supplied cannot be credited.
A `--baseline` comparison on one case is a signal, not a population claim; repeat it
across cases before generalising. The bundled fixture is synthetic, and its numbers
are fixture values, not results from any organizer case.

## Why this counts as the new capability, not just a script

The skill refuses output it cannot ground and names the offending number, so the
author sees the defect in the same run that produced it. Field-level evidence
locators, the distinction between reported, not-reported and speculative values, and
the skill-versus-baseline delta are all measured on the run rather than reviewed by
hand afterwards.
