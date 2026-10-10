# Example evaluation walkthroughs

Use at least two task types or domains. The examples are contracts, not a source
of public test answers.

## Domain A: automated analysis of a measured signal

- **Valid:** includes the required artifact, satisfies physical constraints, and
  reports uncertainty. Show gate results and calculate each metric from the
  declared formula.
- **Invalid:** violates a declared constraint or omits required evidence. Show
  the failed gate and why no ranking score is assigned.
- **Adversarial:** optimizes a proxy with a plausible-looking artifact but fails
  an independent audit. Show the score before the gate and the rejection after it.

## Domain B: simulation-based prediction

- **Valid:** uses only permitted inputs, stays within the compute budget, and
  includes a reproducible seed/configuration. Walk through aggregation and ties.
- **Invalid:** uses withheld information or reports no uncertainty. Show the
  contamination or evidence gate and the resulting ineligibility.
- **Adversarial:** memorizes a near-duplicate public instance. Show the overlap
  detection, corrected evaluation set, and ranking outcome.

## When automatic ground truth is unavailable

Keep the decision `blocked` unless an evidence-acquisition protocol defines an
independent measurement, reviewer qualifications, adjudication, uncertainty,
and cost. A plausible narrative is not an oracle.

## Scoring worksheet

For each example record: task ID, gate outcomes, raw per-instance values, metric
formula and units, aggregation, uncertainty interval, tie policy, and final
eligibility/rank. Use the same worksheet for valid, invalid, and adversarial
cases.
