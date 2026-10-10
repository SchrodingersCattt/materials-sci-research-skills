# Threat model

Treat the evaluator and benchmark release as an attack surface. For each threat,
record the precondition, exploit, scientific harm, detection signal, defense,
and residual risk.

At minimum consider training-data leakage, memorization, near-duplicate tasks,
contamination through public examples, reward hacking, evaluator/parser
exploits, unverifiable self-reported results, cherry-picking, overfitting to a
static question set, and resource-accounting tricks. Include insider and
accidental failure modes where they affect validity.

Defenses may include fresh hidden tasks, provenance and deduplication checks,
held-out audits, sandboxed evaluators, signed artifacts, independent reruns,
randomized task order, rate limits, and disclosure requirements. Explain what a
defense cannot detect; a threat model is not a claim that gaming is impossible.
