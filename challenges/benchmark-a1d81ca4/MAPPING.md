# Mapping: case requirement → mechanism → verification

Task: authoring a literature-reading / academic-writing benchmark (cases, expected answers, scoring).
No official scoring claim is made here.

| Requirement | Mechanism | Evidence |
|---|---|---|
| A case must state what it tests and what it rests on | `validate` requires `id`, `title`, `instruction`, `material`, `expected` and `anchors` per case, and refuses a case with an empty expected-answer contract | `benchmark-report.json`: `problems` naming the missing field |
| The material must actually exist | every `material[].path` is resolved relative to the spec and checked on disk | `problems`: "references missing material <path>" |
| Scoring must be weighted and consistent | every anchor carries `id`, `kind` (`required`/`bonus`/`penalty`), `points` and `text`; earnable weights (required + bonus) must equal the case's `max_points`, and penalties are reported separately | report `cases[].earnable_points`, `penalties`, `problems` ("earnable anchors sum to X but max_points is Y") |
| No duplicated or dangling identifiers | case ids and anchor ids are checked for uniqueness | `problems`: "duplicate case ids", "repeats anchor id" |
| The set must cover more than one kind of task | the spec declares `min_cases`; the number of distinct case kinds is compared with it | `problems`: "declares N case kind(s)" |
| A score must be reproducible, not an impression | `score` matches each anchor against the answer by normalised substring, lists missed required anchors by id, subtracts matched penalties, clips to the maximum, and records both the spec hash and the answer hash | `scoring-report.json` (`results[]`, `total`, `maximum`, `normalised_total`, `method`) |
| A weak answer must score lower | the rubric mixes required, bonus and penalty anchors, so overstating a claim is subtracted rather than ignored | self-test: reference answers reach `normalised_total = 1.0`, weak answers score strictly lower with both penalties matched |
| Re-runnable | `verify` re-validates from the spec, records the spec hash and checks that every case declares anchors and a computable maximum | `benchmark-verification.json` (`structure_valid`, `case_count`, `deterministic`, `scoring_reproducible`) |
| Honest limits | matching is substring-based, the rule is only the one declared, and the score is explicitly not a platform score; unresolved material and ambiguous anchors are named | `scope_note` on every report; `SKILL.md` failure handling |
