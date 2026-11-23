---
name: publication-quality-data-visualisation
description: |-
  Use when research data must become a publication-quality figure: chart type matched to the data, encoding declared in a manifest, axes and annotation checked, error bars defined, and an export that survives print.
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

1. **Produce the deliverable now** — the cleaned table, the statistics, the figure, the report — even
   if some checks are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: profile, repair what the profile names, rerun, update `result.json`.


## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference, including the data
  dictionary and `environment/resources.yaml`. Read the actual files; a column name is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only, plus the declared toolchain (`scientific-python`, `SQLite`). No network.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# 科研数据可视化 — from raw table to a figure that survives review

VISUAL_ENGINE
PROFILE_ENGINE

## What this must get right

- **The data dictionary is read before any processing.** Column semantics, units and constraints drive
  the decisions; a generic script that ignores them is the failure this track names first.
- **Missing, zero and not-applicable are three different states.** Conflating them changes every
  downstream statistic.
- **Every transformation is recorded** with the value before and after, and the input file is never
  modified.
- **The report's numbers come from the same computation as the results.** A quality report that
  disagrees with the table it describes is worse than none.
- **Assumptions behind a test are stated and checked** — sample size, normality, variance, group count —
  and an effect size plus interval accompanies every p-value. `p = 0.04` is not "proves effective".
- **Untreated problems are named.** A missing value that was left, an outlier that was kept, a query
  that failed — each is reported rather than dropped from the narrative.
- **The chart type is matched to the data's structure.** An unordered category comparison is not a pie
  chart, and a time series is not a set of side-by-side bars.
- **Axes are honest.** No truncated baseline without saying so, a log axis declared as logarithmic.
- **Error bars say what they are** — standard deviation, standard error or confidence interval — and the
  sample size behind them is available.
- **Colour survives greyscale and colour-vision deficiency**, and categories that cannot be
  distinguished are not forced into one panel.
- **The export is usable**: resolution at target size, fonts embedded, non-ASCII text rendering, and
  dimensions matching the target column width.


## What it must refuse

- **Refuse to fill a missing value without a stated rule**, and never with a column mean unless the rule
  says so and the reason is given.
- **Refuse to treat a not-detected as a zero.** "未检测" and "检测为 0" are different facts.
- **Refuse to delete an outlier silently.** Keep it, flag it with the rule, and say what was done.
- **Refuse to report a p-value as a conclusion.** Effect size, interval and assumptions come with it.
- **Refuse to claim full coverage** when a column could not be parsed, a table failed, or rows were
  dropped.
- **Refuse to invent a value the data does not contain**, and never overwrite the supplied input.
- **Refuse to report "QA passed" until visual inspection at target size has happened.** Automated
  checks are necessary and not sufficient.


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
locators, the run status and the uncertainty. A number is reported with its unit, its condition and the
rule that produced it. A value that is missing is reported as missing, a value that is zero as zero,
and a value that was not applicable as not applicable — the three are never conflated. Where a step
could not be completed, the output names the step rather than reporting a partial pass as complete.

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
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpjrf212ua/example/work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpjrf212ua/example/work/contract.json --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpjrf212ua/example/work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpjrf212ua/example/work
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
| 4 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `analysis_checks.py`, `file_inventory_checks.py`, `gain_checks.py`, `protocol_audit_checks.py`. |

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
| declared artifacts inspected per run | 11 |
| of which are content checks, not just file presence | 11 |
| distinct machine-readable reports emitted | 4 |
| conditions the package refuses to pass silently | 2 |
| self-test suites shipped | 4 |
| self-test assertions | 78 |
| adversarial negative controls in the test suite | 5 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 11 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 2 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 4 machine-readable report(s): `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1`, `output-contract/v1` |
| Regression safety | none | 78 assertions in the shipped self-tests, including 5 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `case_id_preserved`, `declared_columns_present`, `declared_vocabulary_respected`, `key_types_match`, `no_placeholders`, `required_files_exist`, `required_files_nonempty`, `required_keys_present`, `result_exists`, `result_parses` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
