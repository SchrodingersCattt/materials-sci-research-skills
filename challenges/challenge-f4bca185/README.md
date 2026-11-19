# contract-driven-reading-answers

A skill for the reading/QA tasks (chart and figure reading, literature Q&A, reader client): the
supplied material becomes an answer where every requested item appears once and every reported value
carries a locator and a verbatim quotation that the checker can find in the source.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/reading_contract.py` | the runtime: `contract`, `check`, `verify` |
| `MAPPING.md` | case requirement → mechanism → verification |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | a fixture case plus a compliant and a defective answer |
| `tests/run_checks.py` | positive path and a defective answer that must fail seven checks |

## Requirements

Python 3.10+ and the standard library only. No network, no `pip install`, no PDF/OCR library, no
model call.

## Use

```
python scripts/reading_contract.py contract --case /input/case.json --out work/contract.json
python scripts/reading_contract.py check    --answer work/answer.json --case /input/case.json --outdir work/check
python scripts/reading_contract.py verify   --answer work/answer.json --outdir work/check
```

Exit codes: `0` pass, `3` at least one check failed. `check` writes `reading-check.json` with one
entry per rule; `verify` writes `reading-verification.json`.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

Positive path: the contract lists every requested field and question; the compliant answer passes
11/11 checks. Negative path: the defective answer must fail exactly the seven rules it breaks —
missing field, off-vocabulary status, value on a `not_reported` field, missing locator, non-verbatim
quotation, value digits absent from the quote, and a reported claim with no evidence.

## Scope and limits

- The runtime checks the **contract**, not the reading: coverage, vocabulary, quotation fidelity and
  numeric preservation. Whether the chosen reading of an ambiguous passage is the right one needs
  review, and the report says so.
- Quotation checking is normalised substring matching against the text blocks the case exposes. A
  case that supplies only page images needs its own extraction step first; this runtime will treat an
  unreadable source as `extraction_failed`, not as a missing value.
- Status vocabularies are the case's own; an answer that invents a status is rejected.
- Not an official score and not a substitute for expert review.

## Maintenance

One standard-library script. Extend the rule list and the field discovery (for example additional
contract shapes), not the dependency list, and keep `tests/run_checks.py` green — including the
defective-answer expectations.
