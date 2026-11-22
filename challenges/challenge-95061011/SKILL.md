---
name: source-aligned-multidocument-comparison
version: 1.0.0
description: Compare supplied research documents using a common source-located field matrix and explicit conditions for comparability.
---

> Path note: the evaluator installs this skill at `/skills/weekly-skill`; every `scripts/...` path below is
> relative to the directory of this `SKILL.md`. If the install path differs in a given run,
> resolve the scripts against that directory instead of the literal path.
# Source-aligned multi-document comparison

Read the actual `/input/case.json`, `/input/comparison-workorder.json`, task.md, all supplied corpus documents and the original output_contract. Produce the requested complete multi-document comparison and `/app/output/result.json` with original case_id and required fields. Use supplied sources only; never invent paper identities, measured values, citations, evidence or completed checks. Treat a missing source or unread section explicitly and retain useful partial results.

1. Inventory each actual document and version, the workorder questions and required common fields. Read the relevant full materials, tables, captions and conditions; record what is genuinely read or inaccessible. Construct one common-field matrix with one cell per requested document/field. Each cell keeps the paper's own document ID, exact paragraph/page/table locator, short source quote, original value, units, experimental context and `reported`, `not_reported`, `source_conflict` or `extraction_failed` status. Do not borrow a value or condition from a different paper. Interpret terms using the source and maintain an explicit mapping for synonyms and units; don't assume different labels or different quantities are equivalent.
2. Before any quantitative comparison or synthesis, align the actual task, metric, units, material, pollutant and budget, plus dataset, experimental conditions, denominator, uncertainty and other workorder-specific factors. A shared metric name or similar topic does not establish comparability. If any required factor is unknown, mismatched or not genuinely reported, label the comparison unestablished/noncomparable; show each result separately and preserve its context. Never pool different dyes, datasets, metrics, budgets or incompatible units merely to create an average. Convert units only when explicitly warranted, computed and traceable.
3. For comparable studies, report only justified differences or ranges, specify the comparison baseline and unit, and retain sample sizes/error definitions where supplied. For apparent disagreements, quote both sources and explain which differences in methods or conditions are actually documented versus merely possible explanations. Distinguish observational contrast, stated author interpretation, uncertainty and the agent's inference. Avoid inventing causal explanations or claiming a consensus from a small or incomplete corpus.
4. Produce the requested coherent synthesis plus the complete editable matrix and per-cell evidence/coverage; do not substitute a single-paper summary or a list of links. Record source conflict, not-reported values and extraction failures separately. Ensure every requested field/document has a row, source IDs and paragraph IDs match, and actual numeric/units are quoted accurately. Check the original output contract and all actual file paths.
5. When input has been explicitly normalized to the optional synthetic interface in `examples/`, `/skills/weekly-skill/scripts/check_matrix.py` can flag missing/duplicate matrix cells, nonexistent source IDs/paragraphs, nonverbatim quotes and condition mismatch before a two-record arithmetic comparison. Identical context labels only mean `comparable_subject_to_scientific_review`, not proof of comparable designs; the tool cannot judge scientific semantics, paper completeness or evidence relevance. For different actual schemas, manually adapt a separate intermediate or perform equivalent review; never overwrite the original output contract.
6. If an editable DOCX and rendered PDF/PNG are required, use the provided tools only if actually available. The included pinned doc-forge adapter has a narrow plain-text scope and does not prove scientific accuracy; if unavailable or unsupported, retain editable Markdown/CSV and explicitly report missing conversions as partial. Never install dependencies during official evaluation or claim a render or preview that did not occur.

The included examples/tests are synthetic interface demonstrations, not organizer cases, scientific results or proof of higher benchmark scores. Validate each claim against the actual supplied documents and reread contextual limitations.

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
| 4 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 1 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`. |
| Worked fixtures (`examples/`) | `README.md`, `results.json`, `sources.json`, `targets.json` - realistic shapes you can run end to end before touching real material. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `GAIN-EVIDENCE.md`, `PROVENANCE.md`.

### Maintenance

The engines and their checks are versioned together: `scripts/` and `tests/` move in lockstep, and the
suites named above are the regression tests to run after any edit. `CHANGELOG.md` records what changed
and why. A package that fails its own checks is not a package to submit - the composing repository's
`verify_package.py` is the pre-submission gate.
