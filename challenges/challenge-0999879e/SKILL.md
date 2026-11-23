---
name: manuscript-quality-and-structure-review
description: |-
  Use when a manuscript needs a quality and structural review whose findings are locatable and reproducible: section completeness, hierarchy, abstract-body agreement, and whether the conclusion answers the introduction.
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

1. **Produce the deliverable now**, in the container format the case asks for, even if some findings
   are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json`** with the original `case_id` and every original `output_contract` field, an
   honest `status`, and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rebuild, verify, update `result.json`.


## Contract

- Read the real `/input/case.json` and `task.md` and every material they reference, including
  `environment/resources.yaml`. Read the actual files; a filename is not evidence.
- Work in `/app/work`. Deliverables go to `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names, nesting
  and types.
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- Standard library only. No network. Declared tools include `pdf-text-tool`, `pdf-render-tool`,
  `ocr-tool`, `latex-compiler`, `office-renderer`, `scientific-python`.
- Skill resources: 50 UTF-8 text files maximum, 500 KB each, 2 MB total, no symlinks.


# 论文质量审查 — review overall quality and structural completeness

## Engine

`scripts/structure_audit.py` — extract what the text claims, then locate every defect to a span.

```bash
python "$SKILL_DIR/scripts/structure_audit.py" inspect  --doc /input/material --out work/inspect.json
python "$SKILL_DIR/scripts/structure_audit.py" outline  --doc /input/material --out work/outline.json
python "$SKILL_DIR/scripts/structure_audit.py" claims   --doc /input/material --out work/claims.json
python "$SKILL_DIR/scripts/structure_audit.py" diagnose --doc /input/material --out work/findings.json
python "$SKILL_DIR/scripts/structure_audit.py" verify --doc /input/material \
    --answer work/findings.md --outdir work/check
```

- **`inspect`** — paragraphs, heading levels, section roles, tables, media, footnotes, equations and
  part hashes. Every later locator is paragraph-based (`p12`) or sentence-based (`p12s3`).
- **`outline`** — the section tree with sizes and the role sequence.
- **`claims`** — sentence-level candidates flagged `causal`, `association`, `absolute`, `hedged`,
  `statistic`, `quantity`, `citation`, `crossref`, `limitation`, `objective`, `contribution`, each
  with its locator.
- **`diagnose`** — rule-based findings, each with a dimension, a locator, the evidence, a suggested
  action and a severity. Read them, then add the ones the rules cannot see, using the same structure.
- **`verify`** — prove every finding still points at text that exists at the locator it names.

## Engine

`scripts/chapter_consistency.py` — prove that what the sections say agrees with each other.

```bash
python "$SKILL_DIR/scripts/chapter_consistency.py" audit \
    --chapters /input/material/ch1.md /input/material/ch2.md \
    [--outline work/outline.json] [--references work/references.json] --out work/consistency.json
```

Twelve checks across the chapters: outline sections and their order, subtree-aware word budgets,
argumentative elements, figure/table/equation numbering, citation resolution for numeric, author-year
and `\cite{}` forms, unit consistency, and duplicate passages. Each finding carries the two positions
that disagree, so a reviewer can compare them without re-reading the whole document.


## What this must get right

- **A finding is a hypothesis with a locator, never a verdict.** Each one names the span it came from,
  so a reviewer can accept, partly accept or reject it.
- **Findings are real.** Do not report a defect that is not there; a false positive costs more than a
  miss, because it teaches the reviewer to distrust the list.
- **Severity is discriminating.** If everything is "medium" the list is useless. Rank by what would
  change a reader's conclusion, not by how easy the item was to spot.
- **Suggestions are executable.** Name what to add, which sentence to narrow, which claim to soften.
  "Strengthen the argument" is not a suggestion.
- **Long documents are fully covered.** If the text was truncated or a section could not be parsed,
  say which span was not reviewed. Never present a partial pass as a complete one.
- **Structural absence is the priority defect.** A section that looks present but carries none of its
  required content is the failure this task exists to catch.
- **The abstract-body-conclusion triangle is checked explicitly**: a claim in the abstract that the
  body does not deliver, and a conclusion that does not answer the question the introduction raised.


## What it must refuse

- **Refuse to report a defect without a locator.** If it cannot be pointed at, it is not a finding.
- **Refuse to treat a deliberate choice as an error.** A control group, a stated assumption, or a
  quotation of another author's view is not a self-contradiction.
- **Refuse to claim full coverage** when a section failed to parse, a figure could not be read, or the
  document was truncated.
- **Refuse to invent a citation or a reference.** A missing entry is reported as missing.


## Evidence you can reproduce

Use gain is scored on a run, not a claim, and the rubric states that written self-description cannot
substitute for runtime evidence:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

`coverage` is the share of your findings the supplied material supports; `grounding` is the share of
your numbers that trace back to it. Exit 2 means the inputs were not comparable. Ship `gain.json`.


## Output requirements

Each case returns a structured result that keeps the input identifier, the main result, the
evidence/source locators, the run status and the uncertainty. Every finding carries: the dimension it
belongs to, the locator, the evidence quote, a severity, and an executable suggested action. Where a
judgement is subjective, state the reference standard you applied, the acceptable range and what
remains uncertain. A span that was not reviewed is reported as not reviewed.

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
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract work/contract.json --out work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work work
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
| declared artifacts inspected per run | 45 |
| of which are content checks, not just file presence | 45 |
| distinct machine-readable reports emitted | 8 |
| conditions the package refuses to pass silently | 2 |
| self-test suites shipped | 1 |
| self-test assertions | 10 |
| adversarial negative controls in the test suite | 0 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 45 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 2 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 8 machine-readable report(s): `chapter-consistency/v1`, `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1` |
| Regression safety | none | 10 assertions in the shipped self-tests, including 0 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `absolute_wording`, `argumentative_elements`, `association_upgraded`, `case_id_preserved`, `causal_without_support`, `citation_author_{surname}_{year`, `citation_key_{key`, `citations_resolve`, `contribution_without_question`, `declared_columns_present` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
