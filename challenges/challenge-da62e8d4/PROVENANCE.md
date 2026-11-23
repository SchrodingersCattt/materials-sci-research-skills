# Provenance

## Origin

Built in the session that produced this directory (2026-11-16, Asia/Shanghai) for the period-4
论文复现 (numerical reproduction) challenge. The `v2` suffix marks the second revision of this
candidate: the first version executed the case-supplied methods without bounding them, so this one runs
each method as a separate subprocess with a time limit and a size-capped output directory, and records
what ran.

## Dependencies

| Component | Use | Required |
|---|---|---|
| Python standard library | the entire runtime (`repro_tool.py`, `gain_check.py`) | yes |
| The case's own Python | the reproduction methods are supplied by the case and executed as subprocesses | supplied by the case |
| No network, no third-party packages | the runtime contract forbids both | — |

## What the scripts are

| Script | Provenance | Role |
|---|---|---|
| `scripts/repro_tool.py` | written for this challenge | Runs case-supplied Python methods inside a bounded sandbox (`safe()` confines every path to the input root and refuses absolute or escaping paths), hashes each input and output, and writes an auditable record of what ran, how long it took, and what it produced |
| `scripts/gain_check.py` | shared across the period-4 packages | Measures a written answer against the supplied material on coverage and grounding, with a `--baseline` mode for skill-versus-baseline comparison |
| `tests/test_v2.py` | written for this challenge | Self-test covering the bounded-execution path |
| `tests/gain_checks.py`, `tests/gain_cases/` | shared fixtures | Gain self-test including negative controls (fabricated answer, off-topic answer, hedge-stripped answer) that must score worse than the grounded one |

## Verified evidence

- `tests/test_v2.py` and `tests/gain_checks.py` both pass on the synthetic fixtures in this directory.
  The gain self-test includes its negative controls, so a passing result means the comparison can
  actually discriminate, not merely that it ran.
- Every path the tool writes is recorded with its SHA-256, so a reviewer can confirm the recorded
  artifact is the artifact that exists.
- The `examples/` directory holds synthetic inputs and the transcript under "Minimal call example" in
  `SKILL.md` is the real captured output of running those inputs through the tools.

## Boundaries

- The tool executes methods the **case supplies**; it does not choose a scientific method, and a method
  that fails is reported as failed with its stderr rather than repaired or reinterpreted.
- Time and size limits are enforced, so a method that exceeds them is marked truncated, not silently
  dropped.
- Reproducibility is claimed only for the recorded run: same inputs, same hashes, same outputs in this
  environment. It is not a claim that the underlying science was independently replicated.
- Nothing here is an official score, and `GAIN-EVIDENCE.md` reports fixture measurements, not case results.
