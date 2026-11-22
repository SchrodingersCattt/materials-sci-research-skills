# Changelog — 文献阅读 Benchmark 与评测工具

Channel: `benchmark-a1d81ca4`. Versioning is per candidate directory; the tree hash is recorded in
the session inventory so a submitted bundle can be identified exactly.

## v2 — 2026-11-22

- synced `scripts/benchmark_build.py` with the shared engine library (2026-11-16 16:38, later than
  the copy this package shipped):

  - **an anchor is matched inside the individual answer values, never against the serialised answer
    object.** Anchors were previously matched against `json.dumps(answer)`, so a needle that only
    appeared as a *key* counted as present and a case could be scored without the answer saying
    anything
  - `score` revalidates the spec and refuses to produce a score for an invalid set, instead of
    emitting a number that looks like a result
  - `min_cases` counts cases rather than distinct `kind` values
  - anchor validation is stricter: finite non-negative weights, unique non-empty string ids, a
    non-empty `material` list where each entry carries a resolving path, and an explicit locator
- added `tests/bench_score_checks.py`. The control was run against the previous copy and failed five
  of its seven assertions (both key-only anchors were awarded, an invalid set scored 20/40, a
  two-case set failed `min_cases=2`); against this version it passes all seven
- `SKILL.md` states the two rules the control enforces, and the organizer's revision-2 input
  interface (source-conditioned benchmark-DRAFT workorder, paragraph/table sources, synthetic
  checker logs are not DSH scores)

## v1 — 2026-11-16

- first published build of this candidate for this channel
- runtime is standard library only; no network call, no pip install, no Office suite
- added: reusable templates, reusable item set, check list, rubric map, gain protocol,
  innovation boundary

## Maintenance policy

- extend the check list before adding dependencies
- every change reruns `tests/run_checks.py` and `tests/bench_score_checks.py`; a change that cannot
  keep the negative paths failing is reverted
- a failed reproduction is reported as a failed reproduction, not silently re-tested into a
  pass
