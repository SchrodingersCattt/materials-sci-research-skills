# Mapping: case requirement → mechanism → verification

Task: reading the supplied material into a checkable answer (chart/figure reading, literature Q&A,
reader client). No official scoring claim is made here.

| Requirement | Mechanism | Evidence |
|---|---|---|
| 找得齐 — every requested item is answered, none silently dropped | `contract` enumerates the requested field ids and question ids from the case (or an explicit field/question file) and emits one skeleton entry per id | `contract.json` (`requested_field_count`, `requested_question_count`, `fields[]`, `questions[]`) |
| A guessed value is not an extraction | a field's status must come from the case's own vocabulary (`reported` / `not_reported` / `source_conflict` / `extraction_failed`), and a `not_reported` field may carry no value | checks `status_vocabulary`, `no_value_for_unreported` |
| 保留条件 — values, units, comparators and conditions are preserved | the skeleton carries a `unit` slot per field, and a value's digits must occur inside its own quotation | check `values_come_from_the_quote`; contract `fields[].unit` |
| 提供依据 — every claim has a locator and a short quotation | a `reported` field must carry `paragraph_id`/`locator` plus a `quote`; a `reported` claim must carry `evidence[]`; a conflict must name two locators | checks `reported_fields_have_evidence`, `claims_have_evidence`, `conflicts_carry_both_sources` |
| A quotation must be real | every quotation is compared, whitespace-normalised, against the text blocks the case exposes (paragraphs, sections, materials, files) | check `quotes_are_verbatim` |
| 处理不确定性 — unreported, conflicting and failed reads are distinguished | the vocabulary separates `not_reported`, `source_conflict` and `extraction_failed`; questions separate `answered`, `partial`, `insufficient_evidence`, `input_error` | checks `status_vocabulary`, `question_status_vocabulary` |
| The answer keeps the case's envelope | `verify` confirms the `case_id`, a vocabulary status, and every field the case's own contract requires | `reading-verification.json` (`case_id_preserved`, `status_present`, `present:<field>`) |
| Honest limits | the runtime checks the contract, not the reading; an ambiguous passage, an unreadable source and an unstated unit are reported as uncertainties | `scope_note` on every report; `SKILL.md` failure handling |
