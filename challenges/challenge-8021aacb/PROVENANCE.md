# Provenance

## Origin

Authored in the session that produced this directory (2026-11-15, Asia/Shanghai) for the
paper-structure and logic-optimisation topic. It replaces an earlier candidate whose primary
path required a pinned `doc-forge` installation and an Office suite inside the evaluation
container; this version is standard-library only, so the deliverable does not depend on an
unverifiable runtime assumption.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`zipfile`, `xml.etree`, `re`, `json`, `hashlib`) | the entire runtime |
| the OOXML wordprocessingML part layout | read/written directly; no third-party DOCX library |

No upstream package is vendored, imported or required. The method — locate every finding to a
paragraph/sentence, keep text edits as instructions, prove preservation by hashing the text
stream — is implemented here directly.

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_manuscript.py` (local, Python 3.12) | pass — all eight planted defect rules fire, 1 executable action, 1 paragraph removed, 11/11 verification checks pass, second plan run finds 0 actions |
| `apply` on the fixture | removes only the declared duplicate paragraph; `order_preserved` confirms the survivors are a subsequence of the input |
| unsupported-format path | `apply` refuses with `reason` recorded in `apply-report.json` |

All fixture text is invented for interface testing. No formal case, hidden material or
official score was used to build or validate this skill.

## Boundaries

- Rule-based findings are hypotheses with locators. The skill reports the rule and the
  passage; deciding whether a structural suggestion is right stays with the author.
- Only duplicate-paragraph deletion is executed; every other edit is a located instruction.
- The verification proves preservation and the applied deletions — not scientific validity
  and not an official score.
- Resource budget observed: 7 UTF-8 text files, largest 38 KB, 60 KB total — inside the
  50-file / 500 KB-per-file / 2 MB-total skill resource limits.
