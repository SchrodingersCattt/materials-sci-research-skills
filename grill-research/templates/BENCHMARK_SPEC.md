# Benchmark specification: `<name>`

**Status:** `draft | review | frozen`  
**Schema version:** `<major.minor>`  
**Question provenance:** `<source, date, and links>`

## Research claim and scope

- Open question: `<one falsifiable question>`
- Capability or claim evaluated: `<precise claim>`
- Scientific progress signal: `<what higher quality means>`
- In scope: `<domains, regimes, and limits>`
- Out of scope: `<explicit exclusions>`
- Baselines: `<named baselines and comparison protocol>`

## Topology decision

Compare `single_leaderboard`, `independent_subtracks`, and
`benchmark_suite`. Record the selected model, tracks, whether an overall ranking
is meaningful, the rationale, and rejected alternatives.

## Task and release contract

Define the unit of evaluation, instance distribution, source or generator,
versioned manifest, public/hidden split, release cadence, observability,
allowed tools/data/compute, interaction limits, and required artifacts and
formats. State how task and submission provenance are retained.

## Scientific validity and ground truth

State physical or mathematical constraints, acceptable evidence, the oracle and
its provenance, uncertainty representation, and treatment of invalid, partial,
contradictory, or abstaining submissions. Explain why a high score means the
claim was met.

## Eligibility and evaluation

For each gate and metric give its formula, unit, direction, valid domain,
missing-value rule, per-instance calculation, aggregation, budgets, baselines,
tie-breakers, and uncertainty reporting. Separate eligibility from objectives.

## Threats and defenses

For every metric answer: how could an agent increase the score without genuine
scientific progress? Cover leakage, memorization, duplicates, contamination,
reward hacking, evaluator exploits, unverifiable claims, and static-set
overfitting. Link to `THREAT_MODEL.md`.

## Sustainability and freeze gate

Describe fresh hidden tasks, independent audits, reproducibility, and versioning.
List pending/disputed/blocked questions explicitly. Freeze only after
`python grill-research/scripts/validate_spec.py <spec.json>` recomputes the
schema and static checks, every machine result binds to the specification hash,
evidence paths exist with matching SHA-256 digests, a reviewer evidence artifact
is signed off, and the valid, invalid, and adversarial scoring walkthroughs pass.
