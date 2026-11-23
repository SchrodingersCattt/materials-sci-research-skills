---
name: latex-authoring-and-build
description: |-
  Use when LaTeX source must be written, repaired and compiled: formulas, tables, citations, template adaptation, compile errors and a reproducible build.
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


# LaTeX 写作与编译 — author, repair and compile LaTeX

## Engine

`scripts/evidence_ledger.py` — bind every sentence in the deliverable to a supplied source, so a
statement with no source cannot reach the output unnoticed.

```bash
python "$SKILL_DIR/scripts/evidence_ledger.py" extract --doc /input/material --sources /input     --out work/ledger.json
# ... write work/draft.md, citing ledger entries ...
python "$SKILL_DIR/scripts/evidence_ledger.py" audit --ledger work/ledger.json --out work/audit.json
python "$SKILL_DIR/scripts/evidence_ledger.py" verify --ledger work/ledger.json --sources /input     --out work/verify.json
python "$SKILL_DIR/scripts/evidence_ledger.py" report --ledger work/ledger.json --out /app/output/change-log.csv
```

1. **`extract`** builds the ledger: one record per claim found in the supplied document, each with its
   source locator, the conditions attached to it, and its strength (reported / hedged / not reported).
   `--citation-map` takes an explicit citation-to-source mapping when the material provides one.
2. **`audit`** reports the defects that matter for this channel: a sentence in the draft with no ledger
   record, a record never used, a number that disagrees with its source, and a hedge that was promoted
   to a statement of fact.
3. **`verify`** re-checks the ledger against the sources, so a record cannot cite something that is not
   there.
4. **`report`** emits the modification record the rubric asks for.


## What this must get right

- **Every factual sentence traces to a fact record.** The audit reports untraced sentences, and the
  deliverable is not finished while any remain.
- **Numbers, units and conditions travel together.** A value stated without its condition is a defect,
  because the rubric scores exactly that.
- **Hedging is preserved.** A source that says `may`, `提示` or `suggested` does not become a statement of
  fact in the output, and the audit flags any promotion.
- **Absences are stated as absences.** Where the material does not report something, the deliverable
  says so rather than writing around it.
- **The document compiles**, and the build is reproducible from the delivered sources: no generated
  file is delivered without the source that produces it.
- **Formulas, tables and citations are correct at the source level**, not adjusted in the PDF
  afterwards.
- **Compile errors are diagnosed to a line and a cause**, then fixed, rather than worked around by
  removing the construct.
- **Template adaptation preserves structure**: section levels, numbering, cross-references and the
  bibliography binding survive the change.


## What it must refuse

- **Refuse to write a sentence with no source.** If the material does not support it, it does not go in.
- **Refuse to invent a citation, a number, or a condition.** A missing reference is reported as missing.
- **Refuse to smooth over a conflict.** Two sources that disagree are reported as a conflict for a human
  to resolve, not averaged or silently chosen between.
- **Refuse to present a draft as finished** when the audit still reports untraced sentences.
- **Refuse to delete a construct to make the build pass.** A table that will not compile is a defect to
  fix, not to remove.
- **Refuse to deliver a PDF without its sources**, or sources that do not produce the delivered PDF.


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
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpqf6tgheq/example/work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpqf6tgheq/example/work/contract.json --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpqf6tgheq/example/work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpqf6tgheq/example/work
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
| declared artifacts inspected per run | 12 |
| of which are content checks, not just file presence | 12 |
| distinct machine-readable reports emitted | 6 |
| conditions the package refuses to pass silently | 1 |
| self-test suites shipped | 1 |
| self-test assertions | 10 |
| adversarial negative controls in the test suite | 0 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 12 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 1 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 6 machine-readable report(s): `citation-audit/v1`, `evidence-ledger/v1`, `number-scan/v1`, `output-contract-check/v1` |
| Regression safety | none | 10 assertions in the shipped self-tests, including 0 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `case_id_preserved`, `declared_columns_present`, `declared_vocabulary_respected`, `key_types_match`, `no_placeholders`, `required_files_exist`, `required_files_nonempty`, `required_keys_present`, `result_exists`, `result_parses` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
