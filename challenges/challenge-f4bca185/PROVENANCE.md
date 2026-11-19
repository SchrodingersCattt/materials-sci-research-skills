# Provenance

## Origin

Built in the session that produced this directory (2026-11-15, Asia/Shanghai) for the reading tasks
(chart parsing, literature Q&A, reader client), as a standard-library candidate that does not depend
on a pinned `doc-forge` installation, a PDF library or an OCR service.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`json`, `re`, `hashlib`, `decimal`, `pathlib`) | the entire runtime |
| no PDF/OCR library, no model call, no network | deliberately not used |

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — the compliant answer passes 11/11 checks |
| contract completeness | the fixture's 5 requested fields and 2 questions all appear in the generated contract |
| defective answer | must fail exactly these seven rules: `field_coverage`, `status_vocabulary`, `no_value_for_unreported`, `reported_fields_have_evidence`, `quotes_are_verbatim`, `values_come_from_the_quote`, `question_coverage`, `claims_have_evidence` — all eight are asserted by the self-test |
| envelope verification | `verify` confirms `case_id`, a vocabulary status and the case's required output fields |

The fixture's defective answer is intentionally wrong on each dimension the rubric covers, so the
self-test fails loudly if a rule stops working.

## Boundaries

- The runtime checks the contract (coverage, vocabulary, quotation fidelity, numeric preservation,
  evidence presence). It does not decide whether an ambiguous passage was read correctly.
- Quotation fidelity is a normalised substring test against the text blocks the case exposes; a case
  that supplies only images needs its own extraction step, and an unreadable source becomes
  `extraction_failed` rather than a guessed value.
- Not an official score and not a substitute for expert review.
- Resource budget observed: 5 UTF-8 text files, largest 22 KB, 44 KB total — inside the 50-file /
  500 KB-per-file / 2 MB-total skill resource limits.
