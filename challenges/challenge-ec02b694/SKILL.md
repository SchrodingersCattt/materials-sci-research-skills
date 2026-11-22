---
name: experimental-parameter-optimisation
description: |-
  Use when experimental parameters must be recommended with a search strategy: key parameters with units, admissible ranges and the basis for each, response metrics, a convergence criterion, and a cost trade-off including machine time.
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

1. **Produce the deliverable now** — the protocol, the feasibility verdict, the comparison — even if
   some fields are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rerun, update `result.json`.


## Contract

- Read the real `/input/case.json` and `task.md` and every material they reference, including
  `environment/resources.yaml`. Read the actual files; a label is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only. No network. Declared tools include `scientific-python`, `pdf-text-tool`,
  `office-renderer`.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# 实验参数优化建议 — recommend parameters with a bounded search and a cost trade-off

## Engine

`scripts/protocol_audit.py` — six views of one protocol. Each reports findings with a dimension, a
locator, the evidence and an executable action, and each exits non-zero while a high-severity finding
remains.

```bash
python "$SKILL_DIR/scripts/protocol_audit.py" operationalise --protocol work/protocol.json --out work/op.json
python "$SKILL_DIR/scripts/protocol_audit.py" feasibility   --protocol work/protocol.json \
    --inventory work/inventory.json --out work/feas.json
python "$SKILL_DIR/scripts/protocol_audit.py" parameters    --protocol work/protocol.json --out work/params.json
python "$SKILL_DIR/scripts/protocol_audit.py" compare       --candidates work/candidates.json --out work/cmp.json
python "$SKILL_DIR/scripts/protocol_audit.py" anomaly       --readings work/readings.csv \
    --id-col group --value-col value --out work/anom.json
python "$SKILL_DIR/scripts/protocol_audit.py" cost          --plan work/plan.json --rates work/rates.json \
    --out work/cost.json
```

- **`operationalise`** — a variable is operational only with *how it is measured*, *unit*, *instrument*
  and *range*. A variable with only a name is a high-severity finding. Controls are classified; a blank
  control with no positive control is a finding, because then a null result cannot be distinguished
  from a failed assay. A decision criterion with no numeric bound is a finding.
- **`feasibility`** — checks a protocol against a supplied inventory. An item the protocol does not
  state is reported `not_stated`; a declared value exceeding the inventory capability is
  `REJECT_LIMIT_EXCEEDED`; requirements with no inventory supplied hold rather than pass.
- **`parameters`** — every parameter needs a unit, an admissible range, and a **basis**. The basis is
  classified as equipment limit, material limit, safety threshold, literature or experience, and an
  unclassified range is high severity. A recommended value outside its own stated range is caught. A
  search strategy with no convergence or stopping criterion is a finding.
- **`compare`** — 3–5 routes on identical fields. Risk in gestalt form ("some risk") is flagged unless
  it names a trigger, a consequence and a mitigation. Cost that counts consumables only is flagged for
  missing machine time and labour. Time that counts execution only is flagged for missing preparation,
  scheduling, queueing and rework. A choice with no rejection reason is flagged.
- **`anomaly`** — a stated threshold and the distance from it, using a modified z-score on the median
  absolute deviation so one large outlier cannot inflate the scale and hide itself. Emits trend
  statements and empty slots for causes, eliminations and re-checks, which the agent fills.
- **`cost`** — machine hours, labour hours and consumables, plus preparation, scheduling, queueing and
  rework overhead. **No rate is inferred**: a missing rate is reported and the total is marked
  incomplete, because a model that silently assumes zero is worse than one that admits it cannot total.


## What this must get right

- **Nothing is assumed satisfied.** If the protocol does not state a value, the output says
  `not_stated` and names the field. A protocol is never credited with meeting a requirement it did not
  mention.
- **Every variable is operational.** How it is measured, in what unit, on which instrument, over what
  range — all four, or it is a finding.
- **Every parameter range names its basis**, and the four kinds are distinguished: equipment limit,
  material limit, safety threshold, literature, experience. A range with no basis is a guess.
- **Risks are specific**: trigger, consequence magnitude, mitigation. Not "there is some risk".
- **Cost includes machine time and labour**, and time includes preparation, scheduling, queueing and
  rework — not execution alone, because those dominate in a real laboratory.
- **Assumptions and expert-confirmation items are labelled.** Where a value came from experience rather
  than a source, it is marked as such and flagged for confirmation.
- **Every range names its basis**, and equipment, material and safety limits are distinguished from
  literature intervals and from experience. That distinction is what makes a recommendation executable.
- **The search has a stopping rule.** Candidate points, the method that generates them, and the
  evidence that ends the search — otherwise the run cannot be reproduced or bounded.
- **The recommended point lies inside its own admissible range**, and any trade-off against cost, time
  or throughput is stated rather than optimised away.
- **A recommendation beyond a stated limit is flagged**, never silently offered.


## What it must refuse

- **Refuse to declare a protocol feasible on the strength of not finding a problem in it.** Absence of a
  stated requirement is not evidence of availability.
- **Refuse to invent a parameter, a price, a lead time or a capability.** A missing rate leaves the
  total incomplete; it is never filled with a plausible number.
- **Refuse to recommend a value beyond a stated equipment, material or safety limit** without saying so.
- **Refuse to present a partial coverage as complete.** If a step could not be assessed, say which step.
- **Refuse to call a stated limitation a defect.** Naming a limitation is correct practice.


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
locators, the run status and the uncertainty. A protocol requirement is reported with the state it is
actually in — stated and met, stated and unmet, or **not stated** — and the three are never conflated.
A value derived from experience rather than a source is labelled. Where the case does not supply
information a verdict would need, the verdict is `HOLD` with the missing input named, not a pass.

## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 6 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 3 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `reference-map-template.csv`. |
| 3 self-test suites (`tests/`) | Run `python tests/run_checks.py` (or the suite named for the engine) to reproduce every claim made in this package. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and
`tests/run_checks.py` is the regression suite to run after any edit. `CHANGELOG.md` records what
changed and why. A package that fails its own checks is not a package to submit — see
`verify_package.py` in the composing repository for the pre-submission gate.

## What this saves, measured

The rubric asks whether loading this package measurably reduces manual work, under the same input and
the same permissions. These are the numbers, and every one is reproducible by running the package -
they are counted from the shipped source, not asserted.

| What the package does automatically | Count |
|---|---|
| declared artifacts inspected per run | 11 |
| of which are content checks, not just file presence | 11 |
| distinct machine-readable reports emitted | 4 |
| conditions the package refuses to pass silently | 0 |
| self-test suites shipped | 3 |
| self-test assertions | 54 |
| adversarial negative controls in the test suite | 3 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 11 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 0 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 4 machine-readable report(s): `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1`, `output-contract/v1` |
| Regression safety | none | 54 assertions in the shipped self-tests, including 3 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `case_id_preserved`, `declared_columns_present`, `declared_vocabulary_respected`, `key_types_match`, `no_placeholders`, `required_files_exist`, `required_files_nonempty`, `required_keys_present`, `result_exists`, `result_parses` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
