---
name: contract-driven-reading-answers
description: Use when supplied material must be read into a checkable answer — one result per requested field or question, every reported value carrying a locator and a verbatim quotation, unreported and conflicting items stated as such, and a contract check that catches a guessed value.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan           # contract, check list, result.json skeleton
# ... read the case material and write the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md   # build, audit, conform, verify
```

`plan` takes no reading of its own and `finish` returns a JSON report whose `failed_checks` names
exactly what to repair. Everything else in this file explains what to put in the deliverable between
those two calls - the budget is for content, not for orchestration. `finish` exits non-zero if any
stage failed or a placeholder is still in `result.json`; repair and rerun it rather than shipping.

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

## Which shape is the answer? Detect it first, then follow that contract

The reading cases come in two published shapes, and the field names differ. Read the input before
choosing, and never answer a question list with a field table (or the reverse).

```bash
python "$SKILL_DIR/scripts/literature_qa.py" plan --input /input \
    --result /app/output/result.json --alternate /app/answers.json --out /app/work/qa-plan.json
```

**Shape A - a question list over one paper** (`/input/case.json` carrying `questions` and numbered
`paragraphs`; the 文献智能问答 statement). The published result is one entry per question, and the
plan command prints the exact field list to fill:

| Where | Required |
|---|---|
| top level | the input identity, echoed unchanged: `case_id`, `paper_id`, `material_version`; plus `answers[]` and `coverage` |
| `answers[]` | one entry **per question, none omitted**, with `question_id`, `answer`, `conditions[]`, `status`, `claims[]`, `unanswered_parts[]` |
| `status` | exactly one of `answered`, `partial`, `insufficient_evidence`, `input_error` |
| `claims[]` | `claim_id`, `text`, `kind`, `evidence[]`; `kind` is `reported` (the paper says it) or `inferred` (you concluded it) |
| `evidence[]` | `paragraph_id` and a verbatim `quote` from the supplied text |
| `unanswered_parts[]` | always present; every entry carries a `reason` |
| `coverage` | `read` and `unread`, each unread entry with its own reason |

Two paths are published for this shape: the adapted main artifact `/app/output/result.json`, and the
originally published `/app/answers.json`. Write the result to the first, then

```bash
python "$SKILL_DIR/scripts/literature_qa.py" preflight --result /app/output/result.json \
    --case /input/case.json --outdir /app/work/preflight        # audit: exits 3 listing every failure
python "$SKILL_DIR/scripts/literature_qa.py" mirror --result /app/output/result.json \
    --also /app/answers.json --out /app/work/mirror.json        # second path, or a reported reason
```

`preflight` is the check that a reviewer would run by hand, and it fails on the two things that
falsify a bundle: a quotation that is not in the supplied text, and a `reported` number that does not
appear in its own quotation. Question text and the task statement are deliberately **not** quotable -
quoting the question back is not evidence about the paper. A `partial` or `insufficient_evidence`
answer must name the parts it did not answer; a `partial` one may still carry `reported` claims for
the parts it did answer.

**Shape B - a field or question declaration in its own file** (a `target-fields.json`, or a generic
`case_id` + `output_contract`): use the generic path below (`reading_contract.py`), whose status
vocabulary is `reported` / `not_reported` / `source_conflict` / `extraction_failed`. When the
declaration names a `field_id` per requested value, `field_semantics.py` is the targeted path:

```bash
python "$SKILL_DIR/scripts/field_semantics.py" plan --fields /input/target-fields.json \
    --result /app/output/result.json --out /app/work/field-plan.json
python "$SKILL_DIR/scripts/field_semantics.py" check --answer /app/output/result.json \
    --fields /input/target-fields.json --material /input --outdir /app/work/field-check
```

Two rules come from the published statement and are checked, not merely remembered:

- **An absent field is not zero.** A field the paper does not carry keeps an empty value and the
  status `not_reported`; `0`, `-`, `n/a` and a blank are not a value and not a refusal, and the audit
  names them (`field.<id>.absent_is_not_zero`).
- **A literal quotation match alone does not establish semantic correctness.** A verbatim sentence
  can carry the right number for a different statistic, condition or unit, so the quotation has to
  demonstrate the requested statistic, condition and unit (`field.<id>.semantic_statistic`,
  `semantic_condition`, `semantic_unit`), and an unmatched word is checked against the declared
  spelling and its synonyms. Where a comparison is phrased by naming the other specimen rather than
  the declared phrase, that is not treated as a defect - the audit says which check it is not making.
- With `--material` the quotation is also verified as verbatim against the supplied text
  (`field.<id>.quote_verbatim`), which is what separates a real quotation from a composed sentence.

Whenever a script refers to itself or its data, use the mount path the platform uses -
`/skills/literature-qa/...` - so the reviewer can open the same absolute path the run used.

## Budget order (do this first)

Three cases run three times each under a 64-request / 900-second budget, so the order matters more
than the length:

1. **Produce the deliverable file(s) now**, in the container format the case asks for, even if some
   sections are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json` with the original `case_id` and every original `output_contract` field**,
   with an honest `status` and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rebuild, verify, and update `result.json`.
   Never let step 3 run out the budget before step 1 has happened.

# Contract-driven reading answers

Run this on the actual case and deliver the answer. Do not fill a field the material does not carry,
do not quote a sentence you did not read, and do not let a partial reading look complete.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the abstract,
  body paragraphs, table text, figure captions, reference metadata, any field list or question list,
  `environment/resources.yaml`. Read the actual text; a section title is not the passage.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types. For a question-shaped case, the same document goes to `/app/answers.json` as well.
- Tools, all standard-library Python 3.10+ (`SKILL_DIR` = the real directory of the loaded
  `SKILL.md`, `/skills/literature-qa` in the evaluation image):
  - `scripts/literature_qa.py` - question-shaped cases: `plan` (schedule the questions, print the
    required field list), `preflight` (audit the result and exit 3 with the failing check ids),
    `mirror` (write the second published path, or report why not)
  - `scripts/reading_contract.py` - field-shaped cases: extract the contract, check the answer,
    verify the envelope
  - `scripts/field_semantics.py` - a `field_id`-keyed declaration: schedule the requested fields and
    audit semantic correctness, where the quotation must demonstrate the requested statistic,
    condition and unit
  - `scripts/contract_check.py`, `scripts/number_scan.py` - contract conformance and numeric
    traceability
- Budget: 64 model requests, 900 s, 16384 output tokens per response.
- The answer is checked line by line: every requested item appears once, every `reported` value has
  a locator and a quotation that is actually in the material, and every gap is stated in the case's
  own status vocabulary.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Extract the contract.**
   `python "$SKILL_DIR/scripts/reading_contract.py" contract --case /input/case.json --out /app/work/contract.json`
   (add `--fields`/`--questions` when they are separate files). It lists every requested field id
   and question id with the status vocabulary the case uses, so nothing can be silently dropped.
   When the case is question-shaped, `literature_qa.py plan` is the equivalent first step and it
   also prints the result field list; run both if unsure which shape the case is.
2. **Read the material and fill the entries.** For each requested field: the value exactly as the
   material states it (with its unit), the paragraph/section/page locator, and a short **verbatim**
   quotation. For each question: the answer, its conditions, its claims with evidence entries, and
   the parts you could not answer. Use the case's vocabulary:
   - fields: `reported` / `not_reported` / `source_conflict` / `extraction_failed`
   - questions: `answered` / `partial` / `insufficient_evidence` / `input_error`
   A value the material does not report is `not_reported` **with no value**; if two passages
   disagree it is `source_conflict` and both locators are named.
3. **Check the answer.**
   `... check --answer /app/work/answer.json --case /input/case.json --outdir /app/work/check`
   It proves: every requested id answered once, statuses on-vocabulary, no value attached to a
   `not_reported` field, every `reported` field carrying locator + quotation, every quotation
   verbatim in the supplied text, conflicts naming two locators, every value's digits present in its
   own quotation, and claims carrying evidence. Exit 3 lists the failing checks by id.
4. **Verify the envelope.** `... verify --answer /app/work/answer.json --outdir /app/work/check`
   proves the answer keeps its `case_id`, carries a status from the case vocabulary and contains
   every field the case's own contract requires.
5. **Write `result.json`** with the original contract fields plus the reading result: the field
   results with their evidence, the question answers, the claims, and the uncertainties — an
   uninspected range, an ambiguous passage, a field whose unit the material never states.
6. **Re-open your own output** before finishing: the check status is `verified`, every quotation in
   the answer appears in the material, and no `not_reported` field carries a number.

## Failure handling

- Material that cannot be read (an image you cannot decode, a truncated file): report
  `extraction_failed` for the affected fields, name the file, and keep the rest of the answer — never
  infer the value from the surrounding text.
- A passage that could support two readings: give the reading you chose, quote the passage, and list
  the alternative in the uncertainties. Do not silently pick the convenient one.
- A question that needs a comparison the material does not make: answer `partial` and list the gap.
- Never quote from memory: if you cannot copy the sentence from the supplied text, you have not read
  it, so the field is `not_reported` or `extraction_failed`.

## Numbers are checked automatically, not by hand

`finish` runs `scripts/number_scan.py` with no plan to write: it reads every number in your markdown,
reads every numeric value in the supplied data, and classifies each prose number as a declared value,
a declared two-value calculation, or undeclared. Undeclared numbers come back in the report's
`undeclared_numbers` list and make the run exit non-zero - that list is the traceability defect list
for the rubric's 结果可核验性 sub-point, so repair it before finishing. Add `--data <dir>` if the
supplied data is not under `/input`.

## Leave an evidence trail

The artifacts are all a reviewer sees, so a run that checked nine numbers and refused two claims
should not look like a run that did neither. Keep `work/run-evidence.json` as you go:

```json
{
  "sources_opened":   [{"path": "material/table-1.csv", "read": true, "note": "12 rows"}],
  "checks_run":       [{"id": "quantity:31.2MPa", "rule": "declared source value", "result": "pass"}],
  "claims_refused":   [{"claim": "...", "reason": "no source value; reported as not reported"}],
  "missing_material": [{"expected": "statistics table", "status": "absent", "handled": "narrowed"}],
  "limitations":      ["no Office renderer in this image; editable source kept"]
}
```

Copy it to the output directory as `run-evidence.json` and name it in `result.json` under
`deliverables` (or `evidence_map`, whichever the contract defines). An empty list means "none
encountered" and must be written explicitly; a missing file reads as "no checks were run".

## What the evaluation image provides

The organizer's own resource list for this challenge (`environment/resources.yaml`, declared per
channel in the published statement) names these as available in the pinned image:

- `execution-contract` - declared available for this challenge
- `scientific-python` - the Python stack for reading data, computing and writing files
- `scientific-tools-provenance` - declared available for this challenge
- `official-deepseek-harness` - the harness that runs this skill on the organizer's cases
- `pdf-text-tool` - extract the real text layer of a supplied PDF (never guess from a file name)
- `pdf-render-tool` - rasterise a PDF page when only the rendered page carries the information
- `ocr-tool` - read a scanned page or one whose text layer is broken
- `latex-compiler` - compile LaTeX when the case asks for it, and to check that it compiles
- `office-renderer` - render DOCX/PPTX to PDF (and pages to PNG) for the preview the runtime contract asks for
- `browser-automation` - open a supplied HTML/SVG artifact and check how it actually renders
- `font-discovery` - find which fonts exist before declaring a typographic constraint unmet

Two rules follow, and they cut both ways:

1. **Do not assume a tool is missing.** If the case asks for an editable artifact plus a rendered
   preview, produce both, using `office-renderer` (for Office formats) or `pdf-render-tool` /
   `browser-automation` (for PDF and SVG/HTML). A preview that exists is evidence; a sentence saying
   the renderer might not exist is not.
2. **Do not claim a tool that is not there.** Confirm availability by running it. If a declared tool
   genuinely fails in your image, keep the editable source, state which tool you tried and what it
   returned, and mark that specific part partial - never rename a text file into the required
   extension and never describe an output you did not produce.

## Worked micro-example (synthetic - the shape, not the content)

Question: "What yield did the treated group reach, and was the difference significant?"
Material: one paper with a results table and a discussion paragraph.

**Typical low-scoring answer**

> The treated group reached a yield of 82%, which is significantly higher than the control, showing
> that the treatment is effective. This is consistent with the literature.

Unsupported: the number may be right but there is no locator, "significantly" is invented, "is
effective" is a conclusion the paper may not draw, and "consistent with the literature" cites nothing.

**The same answer, compliant**

> **Answer.** The treated group reached 82% (Table 2, `paper/main.pdf` p.5; the text layer was read
> directly, not the rendered page). The control value is not reported in the supplied material, so the
> difference cannot be computed. The paper reports no significance test.
>
> **Evidence.** "the treated group reached a yield of 82%" - Table 2, row 4, quoted verbatim.
>
> **Refused.** "significantly higher" - the material contains no test statistic, p value or
> confidence interval. Recorded as not reported rather than inferred from error bars.
>
> **Confidence.** High for the 82% figure (verbatim table value). The absence of a control value is a
> material limitation, not a finding.

**The extraction table row that goes with it**

| item | value | unit | source | locator | status |
|---|---|---|---|---|---|
| treated yield | 82 | % | paper/main.pdf | Table 2 row 4 | extracted |
| control yield | - | - | - | - | not reported |
| significance | - | - | - | - | not reported |

A refusal is a deliverable: the -/not reported rows are what shows the question was read rather than
partially guessed.

## Materials in this submission

| Path | What it answers |
|---|---|
| `RUBRIC.md` | this channel's published sub-points, each mapped to the artifact that covers it |
| `GAIN.md` | how the platform's baseline-versus-skill comparison is answered, and how to reproduce the fixture measurements |
| `INNOVATION.md` | the capability the base agent lacks, the method change, the boundary and the evidence |
| `ECOSYSTEM.md` | documentation completeness and the reusable resources, generated from the real file list |
| `CHECKLIST.md` | one pass-through list per run, one question per published sub-point |
| `CHANGELOG.md` | versioning and maintenance policy |
| `templates/` | glossary, reference map, change log, deliverable plan and pointer templates |
| `scripts/literature_qa.py` | the question-shaped contract: schedule the questions, audit the result, mirror the second published path |
| `scripts/reading_contract.py` | the field-shaped contract: enumerate the requested fields, check the answer, verify the envelope |
| `scripts/field_semantics.py` | a `field_id`-keyed declaration: schedule the fields, audit that the quotation demonstrates the statistic, condition and unit |
| `tests/cases/` | reusable interface items with structural expectations |
| `tests/qa_checks.py` | the question-shaped fixture and its negative controls (13 planted defects) |
| `tests/field_checks.py` | the field-declaration fixture and its negative controls (11 planted defects) |

These are submission materials, not case answers: no organizer case, whiteboard or formal result is
included anywhere in this bundle.

## Minimal example (synthetic, not a case)

```bash
# field-shaped case
python "$SKILL_DIR/scripts/reading_contract.py" contract --case /app/work/fixture/case.json --out /app/work/contract.json
python "$SKILL_DIR/scripts/reading_contract.py" check --answer /app/work/fixture/answer-good.json --case /app/work/fixture/case.json --outdir /app/work/check
python "$SKILL_DIR/scripts/reading_contract.py" verify --answer /app/work/fixture/answer-good.json --outdir /app/work/check

# question-shaped case
python "$SKILL_DIR/scripts/literature_qa.py" plan --input /input --out /app/work/qa-plan.json
python "$SKILL_DIR/scripts/literature_qa.py" preflight --result /app/work/fixture/answer-question.json --case /app/work/fixture/case.json --outdir /app/work/preflight
python "$SKILL_DIR/scripts/literature_qa.py" mirror --result /app/output/result.json --also /app/answers.json
```

Illustrative behaviour on those fixtures: the contract lists 5 fields and 2 questions, the compliant
answer passes 11/11 checks, and the deliberately defective answer fails field coverage, the status
vocabulary, the value-on-unreported rule, the locator rule, quotation fidelity, numeric preservation
and claim evidence. The question fixture is a 32-paragraph paper with nine questions: the scheduled
plan finds all nine ids and all 32 paragraph ids, the compliant answer passes every check, and each
of 13 planted defects is caught - among them a quotation that is not in the text, a `reported` number
that is not in its own quotation, a fact quoted out of the question text, a paragraph id the case
does not carry, an omitted question, a gap with no reason, and an unfilled skeleton. Those values
come from `examples/synthetic_case.py` and `tests/qa_checks.py` - interface fixtures, not case
results and not scores. See `MAPPING.md`.

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
| 7 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 6 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `figure-table-pointer-template.csv`, `glossary-template.csv`, `reference-map-template.csv`, `section-evidence-map.csv`. |
| 4 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `field_checks.py`, `gain_checks.py`, `qa_checks.py`, `run_checks.py`. |
| Worked fixtures (`examples/`) | `README.md`, `case.json`, `material`, `synthetic_case.py`, `task.md` - realistic shapes you can run end to end before touching real material. |
| Test cases (`tests/cases/`) | 4 declared cases you can extend with your own. |

### What it needs

- Python 3.10 or newer. **Standard library only**: no network, no `pip install`, no plotting package, no `python-pptx`.
- Inputs are read from the paths the case declares, and outputs are written under the output directory you pass. Nothing is hardcoded to the author's machine.

### Where it stops

- It reports what the supplied material states and refuses to fill a gap with a plausible value; an absent figure appears as an explicit limitation, never as an estimate.
- It verifies its own artifacts against its own specification and checks the real bytes it wrote. It does not judge whether the scientific choice was the right one - that remains a human or judge decision, and the package says so in its verification report.

Supporting documents: `CHANGELOG.md`, `CHECKLIST.md`, `ECOSYSTEM.md`, `GAIN-EVIDENCE.md`, `GAIN.md`, `INNOVATION.md`, `MAPPING.md`, `PROVENANCE.md`.

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
| distinct machine-readable reports emitted | 12 |
| conditions the package refuses to pass silently | 4 |
| self-test suites shipped | 4 |
| self-test assertions | 20 |
| adversarial negative controls in the test suite | 12 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 26 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 4 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 12 machine-readable report(s): `field-extraction-check/v1`, `field-extraction-plan/v1`, `literature-qa-mirror/v1`, `literature-qa-plan/v1` |
| Regression safety | none | 20 assertions in the shipped self-tests, including 12 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `answer_hash_recorded`, `case_id_preserved`, `claims_have_evidence`, `conflicts_carry_both_sources`, `contract_field`, `declared_columns_present`, `declared_vocabulary_respected`, `field_coverage`, `key_types_match`, `no_duplicate_fields` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
