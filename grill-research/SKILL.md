---
name: grill-research
description: "Guides a researcher who wants to turn an open scientific question into an objectively evaluated agent benchmark: elicit the claim, task contract, validity oracle, scoring, threats, and freeze evidence before implementation. Use for leaderboard, task, evaluation, or acceptance-criteria design; do not use for ordinary scientific Q&A, running a benchmark, or optimizing a submission."
---

# Grill Research

`grill-research` is a pre-execution benchmark-design facilitator. It produces a
reviewable Benchmark RFC for a separate forge. It does not generate tasks, run
research agents, judge submissions, or operate a leaderboard.

## Activation and progressive disclosure

Activate when a user asks to turn an open scientific problem into an agent
challenge, define a benchmark or leaderboard, choose task acceptance criteria,
or decide how scientific progress should be measured before implementation.
Do not activate for ordinary scientific answers, implementing an already-frozen
benchmark, executing evaluations, or improving a submission score.

Load only what the current question needs: use
[`references/benchmark-design.md`](references/benchmark-design.md) for topology
and task/release choices; [`references/scientific-validity.md`](references/scientific-validity.md)
for evidence and oracles; [`references/metric-and-ranking-design.md`](references/metric-and-ranking-design.md)
for formulas and ranking; and [`references/threat-model.md`](references/threat-model.md)
for adversarial challenges. Start documents from
[`templates/BENCHMARK_SPEC.md`](templates/BENCHMARK_SPEC.md),
[`templates/BENCHMARK_SPEC.yaml`](templates/BENCHMARK_SPEC.yaml), and
[`templates/DECISIONS.md`](templates/DECISIONS.md). Before freeze, run
`python grill-research/scripts/validate_spec.py <spec.json>` with the pinned
`grill-research/requirements.txt` installed.

## Interview protocol

1. Start with the researcher's open question and record its provenance.
2. Ask one unresolved, high-impact question at a time. Offer concrete options,
   recommend one with a reason, and record the answer before moving on.
3. Establish the claim, intended scientific progress, baselines, scope limits,
   and what would count as evidence.
4. Compare `undecided`, single leaderboard, independent subtracks, and a suite.
   Do not assume an overall ranking is meaningful.
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
10. Stop only when all critical questions are decided, challenged, reviewed, and
    machine-validated. A missing oracle remains blocked.

## Recovery and decision states

Every decision is `decided`, `pending`, `disputed`, or `blocked`; unresolved
questions are explicit records, never silently defaulted. If the researcher
says “unsure” or rejects every option, record `pending` and ask a narrower
question with a new tradeoff. If they revise a decision, append a superseding
record, mark the old record `disputed`, and recompute affected metrics and
threats. If constraints conflict, stop scoring, show the contradiction, and ask
which constraint has priority. Never choose silently.

On pause, persist the RFC and decision log with `status: draft` or `review`,
then resume from the highest-impact pending or blocked question. Refusal or
inability to supply a reliable oracle keeps the affected decision `blocked` and
prevents freeze; propose an evidence-acquisition protocol. A frozen
specification has no unresolved questions, substantive review sign-off, verified
artifacts, and valid/invalid/adversarial examples with scoring walkthroughs.

## Required output bundle

Produce `BENCHMARK_SPEC.md`, `BENCHMARK_SPEC.yaml`, `DECISIONS.md`,
`THREAT_MODEL.md`, and `EXAMPLES.md`, plus a copy of
`schemas/benchmark-spec.schema.json`. Keep the design independent of any
particular benchmark forge. Use the interaction corpus in
[`tests/interaction_evals.json`](tests/interaction_evals.json) to check
activation and recovery behavior. The separate forge may implement task
generation, release, judging, and conformance tests only after the
specification is explicitly frozen.
