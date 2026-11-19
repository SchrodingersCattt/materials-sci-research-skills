# evidence-ledger-writing

A skill for the evidence-driven writing topic: a manuscript's claims are extracted with
locators, matched against the supplied source passages, judged for strength against the wording
those passages actually use, and reported as a re-runnable ledger plus a citation audit.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the instruction the evaluator agent reads first |
| `scripts/evidence_ledger.py` | the runtime: `extract`, `audit`, `report`, `verify` |
| `MAPPING.md` | requirement direction → mechanism → evidence |
| `PROVENANCE.md` | origin, verified evidence, boundaries |
| `examples/synthetic_case.py` | builds the synthetic manuscript + source pack |
| `tests/run_checks.py` | builds the fixture, runs the pipeline, asserts the contract |

## Requirements

Python 3.10+ and the standard library only. No network, no `pip install`, no doc-forge, no
Office suite. Sources may be `.docx`, `.md`, `.txt`, `.json`, `.csv`, `.tsv`, `.yaml`, `.tex`.

## Use

```
python scripts/evidence_ledger.py extract --doc MANUSCRIPT --sources SOURCES --out work/ledger.json
python scripts/evidence_ledger.py audit   --ledger work/ledger.json --out work/citation-audit.json
python scripts/evidence_ledger.py report  --ledger work/ledger.json --out /app/output
python scripts/evidence_ledger.py verify  --ledger work/ledger.json --sources SOURCES --out work/reproducibility.json
```

`extract` writes the ledger; `report` writes the ledger, the citation audit and a human-readable
`EVIDENCE_LEDGER.md` (claim, locator, verdict, strongest evidence, reasons, suggested rewrite);
`verify` re-reads every file the ledger names and compares hashes. Exit code `3` means a hash no
longer matches — the ledger must be regenerated, not silently trusted.

## Self-test

```
python examples/synthetic_case.py --outdir /tmp/fixture
python tests/run_checks.py --workdir /tmp/lab
```

The fixture plants a supported claim, a causal claim whose source only reports an association
and explicitly denies causation, a consensus claim over a single case report, a proof-level
claim against a source that names what it cannot exclude, a claim citing a phantom reference,
an uncited entry and a duplicate DOI. The self-test asserts the strength upgrades are detected,
the three citation findings fire, verification passes, and a second extraction reproduces the
same claim ids and verdict summary.

## Scope and limits

- Evidence matching is content-word overlap plus strength alignment; it locates and compares, it
  does not prove that a source is externally correct. A database lookup is only possible when
  the case supplies or permits one, and is otherwise reported as a limitation.
- Verdicts are stated against the supplied passages only. `supported` means the passage carries
  the sentence; it is not a claim that the passage is right.
- The ledger does not rewrite the manuscript for you: it gives the verdict, the excerpt, the
  reasons and a rewrite direction, and the agent applies the ones the case asks for.
- Not an official score, and not a substitute for peer review.

## Maintenance

Single-file runtime, no third-party imports. Extend the rule sets (`CAUSAL`, `NEGATED_CAUSAL`,
`CONSENSUS`, `SCALE_WORDS`, `LIMIT_WORD`) and the check list, not the dependency list, and keep
`tests/run_checks.py` green — including its expectation of at least three strength upgrades.
