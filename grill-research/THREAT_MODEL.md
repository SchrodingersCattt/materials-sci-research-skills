# Threat model worksheet

A benchmark is not frozen until each material metric has a concrete gaming
challenge and defense. Complete one row per threat and retain residual risk.

| Threat | Precondition and exploit | Scientific harm | Detection signal | Defense | Residual risk |
|---|---|---|---|---|---|
| Leakage or memorization | `<how known data raises score>` | `<claim distorted>` | `<test or audit>` | `<fresh/held-out control>` | `<what remains>` |
| Near-duplicate or contamination | `<overlap path>` | `<generalization overstated>` | `<deduplication check>` | `<provenance and split policy>` | `<what remains>` |
| Reward hacking | `<metric loophole>` | `<invalid result rewarded>` | `<independent validity gate>` | `<constraint/oracle/audit>` | `<what remains>` |
| Evaluator exploit | `<parser or sandbox path>` | `<score detached from science>` | `<differential rerun>` | `<sandbox and signed artifacts>` | `<what remains>` |
| Unverifiable self-report | `<unsupported evidence>` | `<result cannot be reproduced>` | `<artifact/provenance review>` | `<independent rerun>` | `<what remains>` |
| Static-set overfitting | `<fixed questions optimized>` | `<progress does not transfer>` | `<fresh hidden release>` | `<versioned re-benchmark>` | `<what remains>` |
