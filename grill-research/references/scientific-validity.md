# Scientific validity

A benchmark score is useful only when an eligible submission represents the
scientific capability named by the benchmark. Record the claim, domain limits,
physical or mathematical constraints, evidence requirements, and what remains
unknown. Separate an eligibility gate (a submission can be rejected) from a
metric (an eligible submission can be ranked).

For each task, state the ground-truth source and its provenance. An oracle can
be an analytical result, a validated simulation, an experiment, or an expert
review protocol. If no reliable oracle exists, record the missing measurement,
why it matters, and the evidence-acquisition protocol needed before freeze.
Represent uncertainty with units, intervals or distributions, confidence or
credible level, and the aggregation rule. Define abstention, invalid output,
partial evidence, and contradictory evidence before seeing results.

A scientifically invalid submission must not earn a high score through a
metric loophole. Domain constraints, conservation or feasibility checks,
replication requirements, and independent audit evidence belong in hard gates
when they protect the claim.
