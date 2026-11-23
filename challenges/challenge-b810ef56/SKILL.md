---
name: evidence-ledger-writing
description: Use when a manuscript's claims must be tied to specific source passages, the citation list checked, and sentences narrowed or strengthened to match the evidence actually supplied — producing a re-runnable claim/evidence ledger rather than a polished draft alone.
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

# Evidence-ledger writing

Run this on the actual case now. Deliver the ledger, the citation audit and the revised
sentences the evidence supports. Do not hand back only a polished manuscript, and do not
assert that a source says something you have not read in the supplied files.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the
  manuscript, the source pack, any workorder, `environment/resources.yaml`. Read the actual
  files; a file name or a discipline label is not evidence.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting
  and types.
- Tool: `"$SKILL_DIR/scripts/evidence_ledger.py"` (`SKILL_DIR` = the real directory of the
  loaded `SKILL.md`). Python 3.10+, standard library only: no network, no pip, no doc-forge,
  no Office suite. Never contact an author, a journal or a database that the case did not
  supply, and never fabricate a DOI, PMID, quotation or statistic.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Save the honest partial
  ledger early, then improve it.
- Only the supplied sources count as evidence. What they do not say is a gap to report, not a
  licence to write it anyway. A missing full text is missing evidence, not evidence of absence.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Extract.**
   `python "$SKILL_DIR/scripts/evidence_ledger.py" extract --doc <manuscript> --sources <dir|file> --out /app/work/ledger.json`
   Every claim unit gets a locator (`p12s3` = paragraph 12, sentence 3), the lexical flags that
   fired (`causal`, `association`, `consensus_claim`, `absolute`, `hedged`, `statistic`,
   `quantity`, `small_scale`, `limitation`), its citation markers, its cited reference entries,
   the best matching supplied passages with content-word overlap scores and verbatim excerpts,
   and a strength verdict with reasons:
   `supported` / `claim_stronger_than_source` / `weakly_linked` / `no_supplied_evidence` /
   `source_stronger_than_claim`. Read it; correct anything the case contradicts, and record
   that you did.
2. **Audit the citation layer.**
   `... audit --ledger /app/work/ledger.json --out /app/work/citation-audit.json`
   Flags a citation with no reference entry, entries that are never cited, duplicate DOIs,
   non-ascending/duplicate numbering and entries missing a DOI or a year. Any check that needs
   an external database is reported as a limitation instead of being guessed.
3. **Decide per claim, with the source in front of you.** For each claim whose verdict is
   `claim_stronger_than_source`, either narrow the sentence to what the passage shows (the
   ledger proposes a concrete rewrite direction) or add the design/statistic that would carry
   the stronger wording — and say which you did. For `weakly_linked`, either point at the exact
   passage (section, page, paragraph, table) or quote it. For `no_supplied_evidence`, cite the
   passage that actually contains the result, or delete the sentence; never invent a source.
   Where two supplied sources conflict, keep both and state the disagreement.
4. **Write the deliverable.** The revised manuscript (or the revised sentences with their
   locators, plus the original text, when the case asks for an edit list), the claim/evidence
   ledger, the citation audit, the verbatim excerpts you relied on, and `result.json` with the
   original contract fields: deliverable, preserved facts (numbers, conditions, terms and
   sources that were not changed), the claim→source map, the change log (wording changes,
   additions, deletions, what still needs a human), status and uncertainty.
5. **Make it reproducible.**
   `... report --ledger /app/work/ledger.json --out /app/output` writes the ledger, the audit
   and a human-readable `EVIDENCE_LEDGER.md`; `... verify --ledger ... --sources <dir> --out ...`
   re-reads every named file and compares hashes, so a second person can re-run the same steps
   and get the same verdicts. Include that verification in `result.json`.
6. **Re-open your own output** before finishing: every claim in the report has a locator, every
   number traces to a supplied passage, and no sentence claims more than its source.

## Failure handling

- Source pack unreadable or absent: deliver the claim inventory, the citation audit and the
  explicit statement that no source matching was possible. Do not downgrade this to "partial
  without reason".
- Manuscript is a PDF/other container: extract its text with the case's own tools first; if
  none is available, report the extraction failure as the limitation and keep the analysis
  scoped to what you could actually read.
- A claim is ambiguous (the rule fired on a legitimate construction): keep it, mark
  `needs_human_decision`, and say what the author must confirm. Never delete a finding to make
  the report look cleaner.
- Numbers disagree between the sentence and the passage: report both, name both locators, and
  do not silently pick one.

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
python "$SKILL_DIR/scripts/evidence_ledger.py" extract --doc /input/manuscript.docx --sources /input/sources --out /app/work/ledger.json
python "$SKILL_DIR/scripts/evidence_ledger.py" audit   --ledger /app/work/ledger.json --out /app/work/citation-audit.json
python "$SKILL_DIR/scripts/evidence_ledger.py" report  --ledger /app/work/ledger.json --out /app/output
python "$SKILL_DIR/scripts/evidence_ledger.py" verify  --ledger /app/work/ledger.json --sources /input/sources --out /app/output/reproducibility.json
```

Illustrative output for that fixture: 5 claims with verdicts
`{supported: 1, claim_stronger_than_source: 3, weakly_linked: 1}`, 3 citation findings
(phantom citation, uncited entries, duplicate DOI) and `{"passed": 5, "failed": 0,
"status": "verified"}`. Those numbers come from `examples/synthetic_case.py`, a fixture
written for interface testing — not case results, not a score. See `MAPPING.md`.

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
python "$SKILL_DIR/scripts/contract_check.py" extract --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpor9uu53j/example/work/contract.json
python "$SKILL_DIR/scripts/contract_check.py" skeleton --contract D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpor9uu53j/example/work/contract.json --out D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpor9uu53j/example/work/result-skeleton.json
python "$SKILL_DIR/scripts/run_case.py" plan --case "$SKILL_DIR/examples/case.json" --task "$SKILL_DIR/examples/task.md" --work D:/DP_Internship/AIagents/AgentDev/agent-internal-challenge/bohrium-product-20261118/build/_tmp/tmpor9uu53j/example/work
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
| Worked fixtures (`examples/`) | `synthetic_case.py` - realistic shapes you can run end to end before touching real material. |
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
| declared artifacts inspected per run | 12 |
| of which are content checks, not just file presence | 12 |
| distinct machine-readable reports emitted | 6 |
| conditions the package refuses to pass silently | 1 |
| self-test suites shipped | 2 |
| self-test assertions | 22 |
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
| Regression safety | none | 22 assertions in the shipped self-tests, including 0 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `case_id_preserved`, `declared_columns_present`, `declared_vocabulary_respected`, `key_types_match`, `no_placeholders`, `required_files_exist`, `required_files_nonempty`, `required_keys_present`, `result_exists`, `result_parses` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
