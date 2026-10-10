# Metric and ranking design

For every metric record a formula, unit, direction, valid domain, missing-value
rule, per-instance value, aggregation, uncertainty, and interpretation. State
whether it is a hard eligibility gate or an optimization objective. Multiple
objectives need a declared Pareto, lexicographic, constrained, or separate-track
policy; do not smuggle them into an unexplained weighted sum.

Declare resource budgets and normalization. Name baselines and the comparison
protocol. Define ties, minimum sample sizes, confidence intervals or other
uncertainty reporting, and release/version labels. A leaderboard should expose
uncertainty rather than imply a meaningful ordering when intervals overlap.

Before freeze, walk through a valid submission, an invalid one, and a gaming
submission with actual numbers. The walkthrough must show the gate decision,
metric calculation, aggregation, and final ranking outcome.
