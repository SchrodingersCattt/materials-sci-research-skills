---
name: evidence-bound-knowledge-graph
description: |-
  Use when a paper must be turned into a knowledge graph of entities and relations tied to evidence: alias normalisation, relation extraction with a provenance edge, graph export and basic query.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan            # contract, check list, result.json skeleton
# ... read the case material and write the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md
```

`plan` takes no reading of its own. `finish` returns a JSON report whose `failed_checks` names exactly
what to repair, and exits non-zero if a stage failed or a placeholder is still in `result.json`.

## Budget order (do this first)

1. **Produce the deliverable now**, in the container format the case asks for, even if some fields are
   still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rebuild, verify, update `result.json`.
   Never let step 3 exhaust the budget before step 1 has happened.


## Contract

- Read the real `/input/case.json` and `task.md` and every material they reference, including
  `environment/resources.yaml`. Read the actual files; a filename or a discipline label is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Produce a located, useful
  deliverable early and refine it; do not spend the budget on prose about method.
- Standard library only. No network. Declared tools include `pdf-text-tool`, `pdf-render-tool`,
  `ocr-tool`, `latex-compiler`, `office-renderer` and `scientific-python`.
- Skill resources are capped at 50 UTF-8 text files, 500 KB each, 2 MB total, no symlinks.


# 文献知识图谱构建 — extract entities and relations bound to evidence

## Engine

`scripts/reading_contract.py` — read the case's contract, then prove the answer satisfies it while every
value stays traceable to a span of the material.

```bash
python "$SKILL_DIR/scripts/reading_contract.py" contract --case /input/case.json --out work/contract.json
# ... produce work/answer.md from the material ...
python "$SKILL_DIR/scripts/reading_contract.py" check --answer work/answer.md --case /input/case.json     --outdir work/check
python "$SKILL_DIR/scripts/reading_contract.py" verify --answer work/answer.md --outdir work/check
```

1. **`contract`** reads `/input/case.json` and reports the fields and questions the case actually asks
   for. Use it to drive the answer instead of guessing the field set. `--fields` and `--questions`
   accept explicit overrides when the case states them in prose rather than in the contract.
2. **`check`** compares the answer against the contract: which required fields are present, which are
   missing, which carry no locator, and which values cannot be found in the material. It writes its
   report under `--outdir` and names what to repair.
3. **`verify`** re-runs the conformance proof over the repaired answer and exits non-zero while any
   required item is still unresolved.

Read the case's own material with the declared tools (`pdf-text-tool`, `pdf-render-tool`,
`ocr-tool`); the engine does not read PDFs for you, it checks what you extracted.


## What this must get right

- Values are quoted from the material, not paraphrased into them. Units, error terms and statistical
  quantities are carried with the value, not normalised or converted.
- Reading order for multi-column input is resolved before anything is extracted, and the resolved order
  is recorded, because a wrong reading order corrupts every downstream field.
- Complex tables are read by row and column with merged cells reported as merged, not silently
  duplicated or dropped.
- A conclusion, a limitation and a speculative statement are distinguished. Hedged wording
  (`may`, `suggest`, `提示`, `可能`) is quoted with its hedge intact and never promoted to a finding.
- Every extracted field can be traced to a page, paragraph, table row and column, or figure caption.
- **Entities are real objects in the paper**, not plausible domain entities: each node carries the span
  where it appears. A node with no span is a fabrication.
- **Aliases are normalised explicitly**, and the alias set is reported, so two names for one object do
  not become two nodes and one name for two objects does not become one.
- **Every edge carries provenance**: the relation type, the span that asserts it, and whether it is
  stated or inferred. An inferred edge is labelled as inferred.
- **The graph is queryable and exportable**, and the export can be re-validated: it re-imports to the
  same node and edge counts.


## What it must refuse

- **Refuse to invent a locator.** If a value cannot be bound to a span, report it as unresolved rather
  than attaching a plausible-looking reference.
- **Refuse to fill a gap.** Material that does not report a field yields `not reported`, never a
  plausible value, an interpolated one, or a "typically" figure.
- **Refuse to treat absence as evidence.** A field not reported is not evidence that the underlying
  thing was not measured.
- **Refuse to pass OCR noise as content.** If a text layer is missing or garbled, say so and report the
  affected region; do not smooth it into readable text.
- **Refuse to add an edge the paper does not assert or imply.** A plausible relation is not a relation.
- **Refuse to normalise away a distinction the paper makes**, such as two material phases or two
  experimental conditions.


## Evidence you can reproduce

Use gain is scored on a run, not on a claim, and the rubric states that written self-description
cannot substitute for runtime evidence. Measure it:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

It reports `coverage` (the share of your claims the supplied material supports) and `grounding` (the
share of your numbers that trace back to it), and with `--baseline` a skill-versus-baseline delta on the
same material. Exit 2 means the inputs were not comparable — fix the inputs, do not read it as a pass.
Put `gain.json` in the output directory: it is evidence the reviewer can re-run.


## Output requirements

Each case returns a structured result that keeps the input identifier, the main result, the
evidence/source locators, the run status and the uncertainty. Where a locator is available — page,
paragraph, table row and column, or figure caption — record it, and prefer the coarsest locator that
still lets a second person find the value unaided.

A field the material does not report is recorded as **not reported**, never as an empty value and never
guessed. The distinction between a value that is absent and a value that could not be extracted is part
of the deliverable, and both are reported honestly.

## Minimal call example (synthetic - interface only, not an answer)

Row 4 of the organizer's delivery table asks for at least one set of inputs, the invocation, and a
sample output marked as an example. Everything below is **synthetic**: the case id is
`SYNTHETIC-EXAMPLE-0001`, the material invents two rows and deliberately leaves one value
absent, and the transcript under it is the **real captured output** of running these commands in this
package. It demonstrates the interface; it is not an answer to any case, and it is not a score.

### The inputs (`examples/`)

| File | What it is |
|---|---|
| `examples/case.json` | a synthetic case; its output contract declares `confidence`, `evidence_map`, `key_findings`, `limitations`, `summary`, plus the deliverable `findings.csv` |
| `examples/task.md` | the synthetic task text |
| `examples/material/synthetic-material.md` | invented material whose catalyst loading is genuinely absent |

### The invocation

```bash
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpq1pqrnv9/example/work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpq1pqrnv9/example/work/contract.json --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpq1pqrnv9/example/work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpq1pqrnv9/example/work
# ... read examples/material/, write the deliverable and work/result.json ...
```

### Sample output (real transcript from these commands)

Paths in the transcript are written `<WORKDIR>` because they differ on every machine; everything else
is exactly what the commands printed.

| Command | Exit | Output |
|---|---|---|
| `contract_check.py extract` | 0 | `{"keys": 5, "files": 0, "columns": 0, "checklist": 7}` |
| `contract_check.py skeleton` | 0 | `{"keys": ["case_id", "confidence", "evidence_map", "key_findings", "limitations", "summary"]}` |
| `run_case.py plan` | 0 | `{"case_found": true, "contract_names": {"keys": ["summary", "key_findings", "evidence_map", "limitations", "confidence"], "files": [], "columns": []}, "stages": {"contract": 0}}` |

Each command below is one this package actually ships; the transcript under it was produced by running exactly these lines against `examples/`.
`extract` reports how many contract keys, files and columns it found; `skeleton` lists the keys the
result must carry, including `case_id`; `plan` writes the checklist and names what to do next. On a real
case the same commands run against `/input/case.json` and `/input/task.md` unchanged - only the paths
differ, which is exactly why the example is included: it proves the interface works end to end.

The synthetic material's absent catalyst loading exists so the example shows the honest path: the
deliverable must say "not reported", and the audit fails the run if a number appears that the material
never stated.
## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 5 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 3 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `reference-map-template.csv`. |
| 1 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and the
suites named above are the regression tests to run after any edit. `CHANGELOG.md` records what changed
and why. A package that fails its own checks is not a package to submit - the composing repository's
`verify_package.py` is the pre-submission gate.
## What this saves, measured

The rubric asks whether loading this package measurably reduces manual work, under the same input and
the same permissions. These are the numbers, and every one is reproducible by running the package -
they are counted from the shipped source, not asserted.

| What the package does automatically | Count |
|---|---|
| declared artifacts inspected per run | 26 |
| of which are content checks, not just file presence | 26 |
| distinct machine-readable reports emitted | 7 |
| conditions the package refuses to pass silently | 2 |
| self-test suites shipped | 1 |
| self-test assertions | 10 |
| adversarial negative controls in the test suite | 0 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 26 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 2 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 7 machine-readable report(s): `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1`, `output-contract/v1` |
| Regression safety | none | 10 assertions in the shipped self-tests, including 0 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `answer_hash_recorded`, `case_id_preserved`, `claims_have_evidence`, `conflicts_carry_both_sources`, `contract_field`, `declared_columns_present`, `declared_vocabulary_respected`, `field_coverage`, `key_types_match`, `no_duplicate_fields` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
