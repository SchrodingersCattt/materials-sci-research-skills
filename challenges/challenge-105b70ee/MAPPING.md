# Mapping: case requirement → mechanism → verification

Task: reading the supplied material into a checkable answer (literature Q&A, conclusion and data
extraction, multi-document comparison, chart/figure reading). No official scoring claim is made here.

Two published shapes are covered: a **field-shaped** case (`case_id` + `output_contract`, statuses
`reported` / `not_reported` / `source_conflict` / `extraction_failed`) and a **question-shaped** case
(one entry per question, statuses `answered` / `partial` / `insufficient_evidence` / `input_error`).

| Requirement | Mechanism | Evidence |
|---|---|---|
| 找得齐 — every requested item is answered, none silently dropped | `contract` enumerates the requested field ids and question ids from the case (or an explicit field/question file) and emits one skeleton entry per id; `literature_qa.py plan` does the same for the question shape and prints the required field list | `contract.json` (`requested_field_count`, `requested_question_count`, `fields[]`, `questions[]`), `qa-plan.json` (`scheduled_answers[]`, `required_fields`) |
| A missed question is not coverage | `preflight` compares the answers against the case's own question ids and fails `answers.every_question_once` on an omitted or duplicated question, and `answer.<id>.gap_declared` when a `partial` / `insufficient_evidence` answer names no gap | check ids in `preflight.json` |
| A guessed value is not an extraction | a field's status must come from the case's own vocabulary (`reported` / `not_reported` / `source_conflict` / `extraction_failed`), and a `not_reported` field may carry no value; a question's status must be one of the four published values | checks `status_vocabulary`, `no_value_for_unreported`, `answer.<id>.status` |
| An absent field is not zero | for a `field_id`-keyed declaration, a `not_reported` or `extraction_failed` field may not carry `0`, `-`, `n/a` or a blank | check `field.<id>.absent_is_not_zero`; fixture `zero-for-absent`, `dash-for-absent` |
| A literal quotation match is not semantic correctness | the quotation must demonstrate the requested statistic, condition and unit, not merely contain a matching number; synonyms of the declared spelling are accepted, and a slot the audit does not claim to check is stated rather than silently passed | checks `field.<id>.semantic_statistic`, `semantic_condition`, `semantic_unit`, `field.<id>.quote_verbatim`; fixtures `statistic-mismatch`, `condition-missing`, `unit-missing`, `quote-not-verbatim` |
| 保留条件 — values, units, comparators and conditions are preserved | the skeleton carries a `unit` slot per field, and a value's digits must occur inside its own quotation | check `values_come_from_the_quote`; contract `fields[].unit` |
| 提供依据 — every claim has a locator and a short quotation | a `reported` field must carry `paragraph_id`/`locator` plus a `quote`; a `reported` claim must carry `evidence[]`; a conflict must name two locators | checks `reported_fields_have_evidence`, `claims_have_evidence`, `conflicts_carry_both_sources` |
| A quotation must be real | every quotation is compared, whitespace-normalised, against the text blocks the case exposes (paragraphs, sections, materials, files), and a quoted paragraph id must exist in the case | checks `quotes_are_verbatim`, `evidence.<…>.quote_verbatim`, `evidence.<…>.paragraph_id_known` |
| 区分原文报告与推断 | a question-shaped claim carries `kind` (`reported` / `inferred`), and a `reported` claim's numbers must appear in its own quotation, so an inferred value cannot be filed as reported | checks `claim.<…>.kind`, `claim.<…>.numbers_in_quote` |
| Quoting the question is not evidence | the question list and the task statement are removed before the quotable text is built | `material_text` in `scripts/literature_qa.py`; fixture `quote-from-question` |
| 处理不确定性 — unreported, conflicting and failed reads are distinguished | the vocabularies separate `not_reported`, `source_conflict`, `extraction_failed`, `answered`, `partial`, `insufficient_evidence`, `input_error` | checks `status_vocabulary`, `question_status_vocabulary`, `answer.<id>.gap_reason[…]` |
| 阅读范围 — what was read, and what was not | `preflight` requires `coverage.read` to be non-empty and every `coverage.unread` entry to carry a reason | checks `coverage.read`, `coverage.unread_reason[…]` |
| The answer keeps the case's envelope | `verify` confirms the `case_id`, a vocabulary status and every field the case's contract requires; `preflight` confirms the input identity (`case_id`, `paper_id`, `material_version`) is echoed unchanged | `reading-verification.json`, check `identity.<field>` |
| Both published result paths carry the artifact | `literature_qa.py mirror` copies the result to the second path, and reports a path it could not write instead of assuming it worked | `mirror.json` (`mirrored[]`, `skipped[]`) |
| Honest limits | the runtime checks the contract, not the reading; an ambiguous passage, an unreadable source and an unstated unit are reported as uncertainties. The engines are validated on fixtures, and no fixture value is claimed as a case result | `scope_note` on every report; `SKILL.md` failure handling; `tests/qa_checks.py` |
