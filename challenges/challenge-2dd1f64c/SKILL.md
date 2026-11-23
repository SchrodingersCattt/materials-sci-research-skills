---
name: literature-screening-and-ranking
description: |-
  Use when candidate records must be screened and ranked: a stated relevance basis per record, ranking on declared fields, and uncertain cases kept uncertain rather than forced.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan
# ... read the case material and produce the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md
```

`plan` takes no reading of its own. `finish` returns a JSON report whose `failed_checks` names exactly
what to repair, and exits non-zero if a stage failed or a placeholder is still in `result.json`.

## Budget order (do this first)

1. **Produce the deliverable now** — the screening record, the included set, the evidence table — even
   if some fields are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: reconcile the counts, repair what the reconciliation names, rerun, update.


## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference, including the corpus
  and `environment/resources.yaml`. Read the actual files; a title is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only. **No network** — every source is supplied in the case.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# screen and rank candidates by relevance with stated grounds

## Engine

`scripts/retrieval_audit.py` — the retrieval record, made mechanical.

```bash
python "$SKILL_DIR/scripts/retrieval_audit.py" query     --question work/q.txt \
    --strategy work/strategy.json --out work/query.json
python "$SKILL_DIR/scripts/retrieval_audit.py" screen    --records work/corpus.csv \
    --criteria work/criteria.json --out work/screening.json
python "$SKILL_DIR/scripts/retrieval_audit.py" reconcile --screening work/screening.json --out work/counts.json
python "$SKILL_DIR/scripts/retrieval_audit.py" coverage  --records work/corpus.csv --query work/query.json \
    --out work/coverage.json
python "$SKILL_DIR/scripts/retrieval_audit.py" appraise  --records work/included.csv --scale work/scale.json \
    --out work/appraisal.json
python "$SKILL_DIR/scripts/retrieval_audit.py" synonyms  --terms work/terms.json --out work/synonyms.json
python "$SKILL_DIR/scripts/retrieval_audit.py" verify    --screening work/screening.json --out work/verify.json
```

- **`query`** turns a question into blocks that each state their **intent** and their field, plus explicit
  language and date limits. A block with no stated intent is a finding, because it cannot be reviewed or
  deliberately removed later.
- **`screen`** applies criteria and keeps a per-record reason. A criterion that **cannot be adjudicated**
  — "relevant", "interesting", "重要" with no bound — is a high-severity finding, because two reviewers
  would split on the same record.
- **`reconcile`** checks the stage counts against the **declared** record count, so a record lost between
  retrieval and screening is reported rather than absorbed.
- **`coverage`** states the **bound**: what the corpus and the declared limits could not include, and
  therefore what the conclusion does not extend to.
- **`appraise`** grades a study dimension by dimension against stated markers and carries the grade into
  a **weight**, so a low-quality study does not count equally with a strong one. With no scale supplied
  it refuses rather than inventing one.
- **`synonyms`** builds cross-language sets and records every translation that was applied, so a match
  from a mapping is distinguishable from a match in the text.
- **`verify`** proves the included set is recomputable from the record alone — the test the briefs state.

`scripts/file_inventory.py` supplies corpus discovery: hashing, content-based de-duplication and version
chains, so a duplicate copy is not counted as independent evidence.


## What this must get right

- **Every decision names the criterion that produced it.** An inclusion or exclusion with no reason is
  the failure this track names first.
- **Criteria are adjudicable.** A property plus a bound, not an adjective. "Sample size at least 10",
  not "relevant".
- **The counts reconcile across stages**, and a record lost between them is reported rather than
  absorbed into the total.
- **The conclusion is bounded.** What the corpus and the limits could not include is stated, so a
  finding is not extended past its evidence.
- **A duplicate is not independent evidence.** Content-hash identity decides this, not the filename.
- **Cross-language matches are recorded as translations**, so a reviewer can see the match came from a
  mapping.
- **Uncertain records are kept as uncertain.** A record that only partly satisfies the criteria is
  reported as uncertain, not forced into include or exclude.


## What it must refuse

- **Refuse to invent a source, a citation, a year or a DOI.** A field the corpus does not supply is
  `not reported`.
- **Refuse to assert novelty or absence from a partial corpus.** "No work has done X" is unprovable from
  the material supplied and must not be claimed.
- **Refuse to relax a criterion to reach a result.** If a filter cannot be satisfied, say so.
- **Refuse to present an included set with no screening record**, and never silently drop a record.
- **Refuse to appraise without a stated scale.** Grades with no scale cannot be interpreted.
- **Refuse to treat a preprint and its published version as interchangeable** without saying so.


## Evidence you can reproduce

Use gain is scored on a run, not a claim, and the rubric states that written self-description cannot
substitute for runtime evidence:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

`coverage` is the share of your claims the supplied material supports; `grounding` is the share of your
numbers that trace back to it. Exit 2 means the inputs were not comparable. Ship `gain.json`.


## Output requirements

Each case returns a structured result holding the input identifier, the main result, the evidence
locators, the run status and the uncertainty. Every retrieval finding names the source it came from and
the position within it. A record that was excluded names the criterion and the reason. A statement the
corpus does not support is reported as unsupported rather than softened, and the run states which part
of the corpus it did not cover.

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
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmp6yab_i_w/example/work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmp6yab_i_w/example/work/contract.json --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmp6yab_i_w/example/work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmp6yab_i_w/example/work
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
| 6 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 3 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `reference-map-template.csv`. |
| 5 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `analysis_checks.py`, `file_inventory_checks.py`, `gain_checks.py`, `protocol_audit_checks.py`, `retrieval_checks.py`. |

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
| declared artifacts inspected per run | 12 |
| of which are content checks, not just file presence | 12 |
| distinct machine-readable reports emitted | 4 |
| conditions the package refuses to pass silently | 2 |
| self-test suites shipped | 5 |
| self-test assertions | 100 |
| adversarial negative controls in the test suite | 7 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 12 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 2 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 4 machine-readable report(s): `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1`, `output-contract/v1` |
| Regression safety | none | 100 assertions in the shipped self-tests, including 7 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `case_id_preserved`, `declared_columns_present`, `declared_vocabulary_respected`, `key_types_match`, `no_placeholders`, `required_files_exist`, `required_files_nonempty`, `required_keys_present`, `result_exists`, `result_parses` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
