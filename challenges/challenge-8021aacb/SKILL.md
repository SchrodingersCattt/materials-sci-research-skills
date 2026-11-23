---
name: source-located-structural-editing
description: Use when a scientific manuscript needs structural and logic optimisation — problems located to a section, paragraph or sentence, an executable edit list (move, merge, split, narrow), a closed question-to-conclusion chain, and a source pointer for every judgement.
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

## Budget order (do this first)

Three cases run three times each under a 64-request / 900-second budget, so the order matters more
than the length:

1. **Produce the deliverable file(s) now**, in the container format the case asks for, even if some
   sections are still thin. A partial artifact that exists beats a complete plan that does not.
2. **Write `result.json` with the original `case_id` and every original `output_contract` field**,
   with an honest `status` and the uncertainties already known.
3. **Then iterate**: audit, repair what the audit names, rebuild, verify, and update `result.json`.
   Never let step 3 run out the budget before step 1 has happened.

# Source-located structural editing

Run this on the actual case now and deliver the diagnosis, the edit list and the manuscript
you can safely produce. Do not return generic writing principles, and do not hand back a
freshly rewritten paper that the author cannot diff against their own text.

## Contract

- Read the real `/input/case.json` and `task.md` and every material they reference
  (`material.json`, `environment/resources.yaml`, any workorder). Read the actual files.
- Work in `/app/work`; deliverables go in `/app/output`, including `result.json` carrying the
  **original `case_id` and every original `output_contract` field** with the original names,
  nesting and types.
- Tool: `"$SKILL_DIR/scripts/structure_audit.py"`, `SKILL_DIR` being the real directory of the
  loaded `SKILL.md`. Python 3.10+, standard library only: no network, no pip, no doc-forge, no
  Office suite.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Produce a located,
  useful deliverable early and refine it; do not spend the budget on prose about writing.
- A structural judgement is a hypothesis with a locator, never a verdict. Every finding and
  every edit action must carry the passage it came from, so the author can accept, partly
  accept or reject it.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Inventory.** `inspect PATH --out /app/work/inspect.json`. You get paragraph indices,
   heading levels, section roles, tables, media, footnotes, equations, fields, tracked
   changes and part hashes. All later locators are paragraph-based (`p12`) or
   sentence-based (`p12s3`), so a reader can find the exact place.
2. **Outline.** `outline --doc DOC --out /app/work/outline.json`. Section tree with sizes,
   the role sequence (abstract → introduction → methods → results → discussion →
   references), duplicate roles and heading-level anomalies. Compare the role order with what
   the case asks for; a case may deviate deliberately, which is a decision to record, not a
   defect to fix silently.
3. **Claims.** `claims --doc DOC --out /app/work/claims.json`. Sentence-level candidates with
   flags: `causal`, `association`, `absolute`, `hedged`, `statistic`, `quantity`, `citation`,
   `crossref`, `limitation`, `objective`, `contribution` — each with its locator and enclosing
   section role.
4. **Diagnose.** `diagnose --doc DOC --out /app/work/findings.json`. Rule-based findings, each
   with `dimension` (研究问题与贡献主张对齐 / 章节结构与叙事顺序 / 论证链与论据对应 /
   段落关系与重复内容 / 结论边界与表述尺度), `locator`, `evidence`, `suggested_action`, the
   rule that fired, and a severity. Read them and add the ones the rules cannot see — an
   argument that is circular, a section that duplicates another's content in different words,
   a conclusion that answers a question the paper never asked — with the same structure and
   the same locator discipline.
5. **Plan.** `plan --doc DOC --out /app/work/plan.json`. Every finding becomes an action:
   executable deletions for provable duplicates, and `report_only` instructions (move this,
   merge with that, split here, narrow this claim to this strength) for everything that would
   change the author's text. Keep the modes honest: only apply what provably preserves the
   rest of the document.
6. **Apply the safe part.** `apply --doc DOC --plan /app/work/plan.json --outdir /app/work/edit`
   rewrites the package in place, removing only the declared duplicate paragraphs; every other
   part stays byte-identical. Exit code 2 means it refused — read `reason` and keep the plan
   as instructions.
7. **Verify.** `verify --doc DOC --output /app/work/edit/restructured.docx --outdir /app/work/edit`
   proves the package opens, counts sentence occurrences with multiplicity (a removed sentence
   is not excused by an identical copy that survives elsewhere), checks the surviving
   sentences are still a subsequence of the input, binds every removal to a declared action,
   and re-checks tables, media, notes, equations and tracked changes.
8. **Write the deliverables.** Into `/app/output`: the diagnosis (findings), the edit plan
   with locators and instructions, the restructured document when you produced one, the
   verification report, and `result.json` with the original contract fields — deliverable
   paths, preserved facts, the claim→evidence/source mapping, the change log (what was applied,
   what awaits the author, what needs a human decision), honest status and uncertainty
   (uninspected ranges, rules that fired ambiguously, deviations the case made deliberately).
9. **Re-open your own output** before finishing: paths resolve, the document opens, and every
   number or claim in `result.json` traces to a finding or a check.

## What makes this different from generic advice

- **诊得准**: every finding names a locator and the rule that fired, so it can be checked.
- **改得动**: the plan is an action list (delete `p10`, move `p12s3` to the discussion,
  narrow the causal verb in `p15s1`), not a rewritten draft.
- **链得通**: the objective, contribution, results and conclusion sentences are extracted
  with locators, so you can show where the chain breaks instead of asserting that it does.
- **说得清**: `verify` counts what changed and proves the rest did not.

## Failure handling

- Not DOCX: analysis runs on extracted text; the plan stays a located instruction list and
  `apply` refuses with `reason` recorded. Never claim a document was edited when it was not.
- Manuscript text looks truncated or the case marks it partial: limit findings to the
  inspected range and say which sections were out of scope. Never report an unseen section as
  missing.
- A finding is ambiguous (the rule fired on a legitimate construction): keep it, mark
  `needs_human_decision`, and say what the author should confirm. Do not delete findings to
  make the report look cleaner.
- Contradiction between the case's own requirements and the manuscript ordering: preserve the
  author's content, record the conflict, and ask for the decision.

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

Material: `material/table-1.csv` with `A,31.2,MPa` and `B,24.0,MPa`, plus `material/stats-note.md`
which states that no significance test was run.

**Typical low-scoring paragraph**

> Both specimens showed strong mechanical performance. Specimen A reached 31.2 MPa, significantly
> higher than B at 24.0 MPa, demonstrating that the treatment improves strength by 30%.

Three defects, each of which the audit and the rubric both punish: "significantly" reports a test the
material does not contain; "by 30%" is an undeclared calculation (and the base is unstated); and
"demonstrating that the treatment improves" turns a two-specimen comparison into a causal claim.

**The same content, compliant**

> Specimen A reached 31.2 MPa and specimen B reached 24.0 MPa (Table 1; `material/table-1.csv`, rows
> A and B). The difference is 7.2 MPa in favour of A, computed from the two declared values in
> compatible units and rounded to one decimal place. Because the material reports no significance
> test, no difference is claimed here in statistical terms.

Every number in the second version is either a declared source value (31.2, 24.0), a declared
compatible-unit calculation (7.2, declared rounding), or absent. The limitation is stated in the same
sentence as the comparison rather than buried later.

**Its evidence map rows**

| claim_id | claim_quote | source_file | locator | strength |
|---|---|---|---|---|
| C-001 | "Specimen A reached 31.2 MPa" | material/table-1.csv | row A, value column | supported |
| C-002 | "The difference is 7.2 MPa" | derived | 31.2 - 24.0, compatible units | supported (declared calculation) |
| C-003 | "the material reports no significance test" | material/stats-note.md | full document | supported (documented absence) |

**The discussion sentence that pairs with it** (one finding, one supplied source, verdict stated):

> The direction of the difference agrees with the supplied literature (`literature/ref-1.md`, §3),
> which reports the same ordering at a different load. That source does not supply a mechanism, so no
> mechanism is proposed here.

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
| `tests/cases/` | reusable interface items with structural expectations |

These are submission materials, not case answers: no organizer case, whiteboard or formal result is
included anywhere in this bundle.

## Minimal example (synthetic, not a case)

```
python "$SKILL_DIR/scripts/structure_audit.py" diagnose --doc /input/manuscript.docx --out /app/work/findings.json
python "$SKILL_DIR/scripts/structure_audit.py" plan     --doc /input/manuscript.docx --out /app/work/plan.json
python "$SKILL_DIR/scripts/structure_audit.py" apply    --doc /input/manuscript.docx --plan /app/work/plan.json --outdir /app/work/edit
python "$SKILL_DIR/scripts/structure_audit.py" verify   --doc /input/manuscript.docx --output /app/work/edit/restructured.docx --outdir /app/work/edit
```

Illustrative output for that fixture: 12 findings across all five dimensions, 1 executable
duplicate deletion with the other 11 as located instructions, then
`{"passed": 11, "failed": 0, "status": "verified"}`. Those numbers come from
`examples/synthetic_manuscript.py`, a fixture written for interface testing — not case
results, not a score. See `MAPPING.md` for the requirement-to-runtime mapping.

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
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpzgnc0fj8/example/work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpzgnc0fj8/example/work/contract.json --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpzgnc0fj8/example/work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpzgnc0fj8/example/work
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
| 6 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `figure-table-pointer-template.csv`, `glossary-template.csv`, `reference-map-template.csv`, `section-evidence-map.csv`. |
| 2 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`, `run_checks.py`. |
| Worked fixtures (`examples/`) | `synthetic_manuscript.py` - realistic shapes you can run end to end before touching real material. |
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
| declared artifacts inspected per run | 31 |
| of which are content checks, not just file presence | 31 |
| distinct machine-readable reports emitted | 7 |
| conditions the package refuses to pass silently | 0 |
| self-test suites shipped | 2 |
| self-test assertions | 20 |
| adversarial negative controls in the test suite | 0 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 31 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 0 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 7 machine-readable report(s): `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1`, `output-contract/v1` |
| Regression safety | none | 20 assertions in the shipped self-tests, including 0 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `absolute_wording`, `association_upgraded`, `case_id_preserved`, `causal_without_support`, `contribution_without_question`, `declared_columns_present`, `declared_vocabulary_respected`, `duplicate_paragraph`, `duplicate_section`, `heading_level_anomaly` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
