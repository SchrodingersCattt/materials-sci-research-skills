# Benchmark design

Begin with the capability or claim, not a preferred leaderboard shape. Compare
single-leaderboard, independent-subtrack, and suite designs against the claim:
coverage, comparability, incentives, and whether a scalar ranking is honest.
Record the selected topology and rejected alternatives.

Define one task instance completely: source or generator, sampling frame,
version, train/public/hidden split, release timing, observables, allowed tools,
data and compute budgets, interaction limits, and required submission files.
State which information is withheld and how fresh tasks are produced. A separate
forge may implement these rules, but it must not invent missing policy.

Use stable identifiers and versioned manifests. Preserve raw task provenance and
submission hashes so an independent party can reproduce an evaluation without
access to private organizer state.
