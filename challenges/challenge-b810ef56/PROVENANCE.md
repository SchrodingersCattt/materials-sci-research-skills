# Provenance

## Origin

Authored in the session that produced this directory (2026-11-15, Asia/Shanghai) for the
literature-evidence-driven writing topic. It replaces an earlier candidate whose primary path
required a pinned `doc-forge` installation inside the evaluation container; this version is
standard-library only, so nothing in the deliverable depends on an unverifiable runtime.

## Dependencies

| Component | Use |
|---|---|
| Python standard library (`zipfile`, `xml.etree`, `re`, `json`, `hashlib`) | the entire runtime |
| the OOXML wordprocessingML part layout | read directly for `.docx` input |

No upstream package is vendored, imported or required. No third-party DOCX library, no network
call, no external database lookup.

## Verified evidence

| Evidence | Result |
|---|---|
| `tests/run_checks.py` on `examples/synthetic_case.py` (local, Python 3.12) | pass — 5 claims extracted with locators, verdicts `{supported: 1, claim_stronger_than_source: 3, weakly_linked: 1}`, 3 citation findings, verification `5/5`, second extraction reproduces identical claim ids and verdict summary |
| planted defects recognised | causal upgrade over an association-only source (which explicitly denies causation), consensus wording over a single case report, proof-level wording against a passage that names what it cannot exclude, phantom citation with no reference entry, uncited entries, duplicate DOI |
| `verify` | re-reads the manuscript and each source file and compares the recorded hashes |

All fixture text is invented for interface testing. No formal case, hidden material or official
score was used to build or validate this skill.

## Boundaries

- Overlap-based matching plus strength alignment locates and compares; it cannot prove a source
  exists or is externally correct. When the case does not supply or permit a database, that
  check is reported as a limitation rather than guessed.
- `supported` means the passage carries the sentence. It is not a scientific verdict about the
  passage.
- The ledger gives verdicts, excerpts, reasons and rewrite directions; applying a rewrite to
  the author's text is a decision the case and the author own.
- Resource budget observed: 7 UTF-8 text files, largest 35 KB, 55 KB total — inside the
  50-file / 500 KB-per-file / 2 MB-total skill resource limits.
