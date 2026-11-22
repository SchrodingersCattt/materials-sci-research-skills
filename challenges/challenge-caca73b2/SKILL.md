---
name: precise-results-and-discussion
version: 1.0.0
description: Write evidence-linked Results and Discussion sections with correct quantitative comparisons, scoped interpretation and editable deliverables.
---

> Path note: the evaluator installs this skill at `/skills/weekly-skill`; every `scripts/...` path below is
> relative to the directory of this `SKILL.md`. If the install path differs in a given run,
> resolve the scripts against that directory instead of the literal path.
# Precise Results and Discussion

Complete the actual requested writing; don't merely describe a plan. Inspect `/input/case.json`, the actual task.md, output_contract, `environment/resources.yaml`, all supplied data, figure panels, captions, statistics and literature relevant to the requested scope. Preserve case_id and original result fields, and put real editable Results and Discussion sections, evidence/quantity mappings, limitations and `/app/output/result.json` under `/app/output`. Keep material read failures and unsupported content explicit; never invent raw values, sample size, error-bar meaning, p-values, paper citations, results, output files, renders or scores.

1. Make a compact source ledger per actual finding: figure/table/source locator, group and comparison, measurement, units, time/dose/conditions, sample size, uncertainty/error-bar definition and reported statistical test. Record what was actually readable. Use source data tables before estimating from plots; an illegible graph is not precise data. Inspect all relevant panels and captions and retain negative or conflicting findings, not only favorable results.
2. Draft substantive Results around the questions and actual figure order. Report magnitude/direction only when supported; compute absolute change and percentage from compatible source values with the correct denominator, and keep units and meaningful precision. Describe differences as statistically significant only when the supplied analysis supports that conclusion. An absent p-value is not p=0; a non-significant result is not proof of equivalence. Separate observations from interpretation.
3. Draft substantive Discussion connecting each major finding to the supplied, actually read literature or to a clearly marked hypothesis. Preserve source context and contrasts, limitations, alternate explanations and disagreements. Do not infer causation from correlation, or convert an untested mechanism into fact. Explicitly distinguish observed findings, qualified interpretation and missing evidence. Respect the actual audience, section lengths, figure references, citation style and author-supplied constraints.
4. Independently trace each actual numeric statement to the correct row/panel, unit, comparator and calculation; check citations against the referenced supplied source and verify that they support the sentence. On explicitly normalized CSV-based cases only, optionally run the genuine local source/quantity adapter `/skills/weekly-skill/scripts/quantity_audit.py` using the plan interface described in `MAPPING.md`. The helper checks declared lexical quantities, units and arithmetic; it cannot interpret plots, determine significance, validate scientific meaning or verify literature support. A helper pass is not formal case success. For unsupported inputs perform appropriate manual or available-tool review and report limitations.
5. Produce an editable Markdown or Word deliverable according to the actual workorder. If real DOCX and PDF/PNG previews are requested, use verified preinstalled tools and inspect actual rendered pages; the included doc-forge adapter is optional and only supports a narrow subset when its genuine pinned runtime is already available. If conversion or rendering is unavailable, preserve the complete editable text and report missing requested artifacts as partial. Never install new dependencies during evaluation or claim a render without producing and inspecting it.

Synthetic examples in `MAPPING.md` are interface demonstrations only, not official cases, baseline comparisons or evidence of score improvement. Save useful partial work early. The actual task contract and original scientific inputs always take priority over helper formats.

<!-- gain-evidence:begin -->
## Evidence you can reproduce (do this before you finish)

The comparison this channel scores under 使用增益 and 创新增益 is measurable, so measure it
instead of describing it. After the deliverable exists:

```bash
python "$SKILL_DIR/scripts/gain_check.py" --source /input --answer /app/output/result.json \
    --baseline work/baseline-answer.md --out /app/work/gain.json
```

It reports `coverage` (how many of your claims the supplied material supports) and
`grounding` (how many of your numbers trace back to it), and with `--baseline` a
skill-versus-baseline delta on the same material. Exit 2 means the inputs were not
comparable - fix the inputs, do not read it as a pass. Put the resulting `gain.json` in the
output directory: it is runtime evidence the reviewer can re-run, which prose cannot replace.
<!-- gain-evidence:end -->

## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 3 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 1 self-test suites (`tests/`) | Run `python tests/run_checks.py` (or the suite named for the engine) to reproduce every claim made in this package. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `GAIN-EVIDENCE.md`, `MAPPING.md`, `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and
`tests/run_checks.py` is the regression suite to run after any edit. `CHANGELOG.md` records what
changed and why. A package that fails its own checks is not a package to submit — see
`verify_package.py` in the composing repository for the pre-submission gate.
