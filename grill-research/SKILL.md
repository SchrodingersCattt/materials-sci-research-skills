---
name: grill-research
description: "Use before implementing or releasing a scientific benchmark to interrogate its purpose, task contract, validity, scoring, threats, and freeze evidence."
---

# Grill Research

`grill-research` is a pre-execution benchmark-design facilitator. It produces a
reviewable Benchmark RFC for a separate forge. It does not generate tasks, run
research agents, judge submissions, or operate a leaderboard.

## Protocol

1. Start with the researcher's open question and record its provenance.
2. Ask one unresolved, high-impact question at a time. Offer concrete options,
   recommend one with a reason, and record the answer before moving on.
3. Establish the claim, intended scientific progress, baselines, scope limits,
   and what would count as evidence.
4. Compare benchmark topologies explicitly: one leaderboard, independent
   subtracks, or a suite. Do not assume an overall ranking is meaningful.
5. Specify the task interface: unit, distribution, sourcing/generation,
   release, observability, tools/data/compute, and submission artifacts.
6. Specify validity and ground truth: physical constraints, evidence, oracle,
   uncertainty, abstention, and failure handling.
7. Specify eligibility gates, metric formulas and units, direction, aggregation,
   objectives, budgets, baselines, ties, and uncertainty reporting.
8. Challenge every important metric with leakage, memorization, duplicates,
   contamination, evaluator exploits, reward hacking, and unverifiable claims.
9. Specify fresh hidden tasks, independent audits, reproducibility, and version
   policy. Keep evidence and provenance beside each material decision.
10. Stop only when all critical questions are decided, challenged, and reviewed.

## Decision states and freeze

Every decision is `decided`, `pending`, `disputed`, or `blocked`; unresolved
questions are explicit records, never silently defaulted. The output status is
`draft`, `review`, or `frozen`. Completing an interview never implies readiness.
A frozen specification has no unresolved material questions, substantive review
sign-off, valid/invalid/adversarial examples with scoring walkthroughs, and a
passing schema/static check. If an implementation reveals a flaw, reopen and
version the RFC; never silently change task or scoring rules.

## Required output bundle

Produce `BENCHMARK_SPEC.md`, `BENCHMARK_SPEC.yaml`, `DECISIONS.md`,
`THREAT_MODEL.md`, and `EXAMPLES.md`, plus a copy of
`schemas/benchmark-spec.schema.json`. Keep the design independent of any
particular benchmark forge. An honest missing oracle remains `blocked`.

Use the deterministic checks in `tests/test_spec_validation.py` (or the
repository's equivalent) before requesting scientific review. A separate forge
must implement task generation, release, judging, and conformance tests only
after the specification is explicitly frozen.
