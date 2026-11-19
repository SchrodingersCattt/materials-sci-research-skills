# Changelog — 写作19｜思维导图

Channel: `challenge-9313ad0a`. Versioning is per candidate directory; the tree hash is recorded in
the session inventory so a submitted bundle can be identified exactly.

## v1 — 2026-11-16

- first published build of this candidate for this channel
- runtime is standard library only; no network call, no pip install, no Office suite
- added: reusable templates, reusable item set, check list, rubric map, gain protocol,
  innovation boundary

## Maintenance policy

- extend the check list before adding dependencies
- every change reruns `tests/run_checks.py`; a change that cannot keep the negative paths
  failing is reverted
- a failed reproduction is reported as a failed reproduction, not silently re-tested into a
  pass
