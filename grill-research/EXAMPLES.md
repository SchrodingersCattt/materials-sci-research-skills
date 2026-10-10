# Example evaluation walkthroughs

These are executable design examples: each one states the input, gate result,
formula, numeric calculation, and outcome. They also show the interview behavior
when a choice is missing or later revised.

## Domain A: measured signal analysis

**Contract:** error is `mean(abs(prediction - reference))`, lower is better;
submissions with a failed evidence gate are ineligible.

**Valid.** References are `[10, 20, 30]`, predictions are `[11, 18, 33]`, and
reported uncertainty is present. Absolute errors are `[1, 2, 3]`; the score is
`(1 + 2 + 3) / 3 = 2.0 task-units`. The artifact and independent rerun gates
pass, so the submission is eligible with score `2.0`.

**Invalid.** The same predictions omit the required provenance hash. The error
would still be `2.0`, but the provenance gate fails, so the submission receives
no rank and the report records `eligible: false`.

**Adversarial.** A submission reports `[10, 20, 30]` for the three public
examples and claims score `0.0`, while the hidden audit contains reference
`[12, 20, 30]`. The audit error is `2 / 3 = 0.667`; public memorization is
recorded as a threat and the hidden score replaces the public score.

## Domain B: simulation-based prediction

**Contract:** a run must stay within 60 seconds and report a 95% interval;
objective score is normalized RMSE, `sqrt(mean((p-r)^2)) / scale`.

**Valid.** For references `[2, 4]`, predictions `[3, 5]`, and `scale = 2`,
RMSE is `sqrt((1 + 1) / 2) = 1`; normalized score is `1 / 2 = 0.5`. The
runtime is 42 seconds, the interval is present, and all gates pass. A second
run with the same seed reproduces the artifact.

**Invalid.** A run takes 75 seconds. The numerical score may be `0.5`, but the
budget gate fails and the result is ineligible; no metric is used to hide that
failure.

**Adversarial.** A system copies a near-duplicate public instance and reports a
perfect score. Similarity audit identifies the overlap; the instance is removed
from the public estimate and a fresh hidden instance determines eligibility.

## No reliable oracle: blocked path

Researcher: “We want to score explanations of a new phenomenon, but no
independent measurement or adjudication protocol exists.”

Agent: “The oracle is unresolved, so I mark `scientific_validity.oracle` as
`blocked`. Would you prefer (A) commission an independent measurement with a
specified uncertainty budget, or (B) define an expert adjudication panel with
qualifications and disagreement rules?”

Researcher: “Neither is funded yet.”

Agent: “I record the decision as `blocked`, preserve both options in
`DECISIONS.md`, and keep status `review`; I will not invent a score or freeze
this benchmark.”

## Multi-turn recovery and revision

Researcher: “Use one leaderboard.”

Agent: “That is a decision candidate. Before recording it, should tasks with
different oracles share a rank, or should they be independent tracks?”

Researcher: “I am unsure.”

Agent: “I record `topology` as `pending` and ask one narrower question: do you
want a single rank only when units, validity gates, and scientific meaning are
shared?”

Researcher: “Actually, use independent tracks.”

Agent: “I append a superseding decision, mark the earlier candidate `disputed`,
recompute ranking and threat questions, and continue from the next unresolved
high-impact item.”

If the researcher rejects every option, introduces incompatible constraints, or
pauses, the agent records the state and resumes from the highest-impact blocker;
it never silently fills the gap.
