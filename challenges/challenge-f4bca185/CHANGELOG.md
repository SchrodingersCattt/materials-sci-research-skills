# Changelog — reading engine (文献智能问答, 结论与数据提取, 多文档比较与整合, 图表解析 …)

Versioning is per candidate directory; the tree hash is recorded in the session inventory so a
submitted bundle can be identified exactly. The engine is shared by the reading channels, so it is
described channel-neutrally: which shape a case has is detected at run time, not assumed from the
channel name (see `SKILL.md`, "Which shape is the answer?").

## v2 — 2026-11-22

- added `scripts/literature_qa.py` for the **question-shaped** contract: `plan` schedules one entry
  per question and prints the required field list, `preflight` audits the produced document, `mirror`
  writes the second published result path or reports why it could not
- `preflight` fails on the defects that falsify a bundle: a quotation that is not in the supplied
  text, a `reported` number that is not in its own quotation, a fact quoted out of the question text
  or the task statement, a paragraph id the case does not carry, an omitted or duplicated question, a
  gap without a reason, an off-vocabulary status, a changed input identity, a claim with no evidence
- added `tests/qa_checks.py`: a 32-paragraph / nine-question fixture. The compliant answer passes
  every check and each of 13 planted defects is caught, four of them by exactly one check id
- added `scripts/field_semantics.py` for a `field_id`-keyed declaration: `plan` schedules one entry
  per requested field, `check` audits coverage, the status vocabulary, "an absent field is not zero",
  verbatim quotations against the supplied material, and that the quotation demonstrates the
  requested statistic, condition and unit rather than merely containing a matching number
- added `tests/field_checks.py`: a 20-field fixture across three papers; the compliant extraction
  passes 145 checks and each of 11 planted defects is caught, eight of them by exactly one check id
- `SKILL.md` now states the two published result paths for this shape (`/app/output/result.json`,
  `/app/answers.json`) and the mount path the platform uses (`/skills/literature-qa`)
- `RUBRIC.md`, `ECOSYSTEM.md`, `PROVENANCE.md` no longer name a single channel for a shared engine;
  `RUBRIC.md` maps this channel's published output contract to the named checks

## v1 — 2026-11-16

- first published build of this candidate for this channel
- runtime is standard library only; no network call, no pip install, no Office suite
- added: reusable templates, reusable item set, check list, rubric map, gain protocol,
  innovation boundary

## Maintenance policy

- extend the check list before adding dependencies
- every change reruns `tests/run_checks.py` and `tests/qa_checks.py`; a change that cannot keep the
  negative paths failing is reverted
- a failed reproduction is reported as a failed reproduction, not silently re-tested into a
  pass
