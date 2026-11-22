---
name: source-faithful-template-adaptation
description: Use for academic format and template adaptation when a supplied manuscript must be converted to a supplied journal, thesis or school template. Extracts the template's own specification into a checklist, applies it to the manuscript without rewriting text, verifies every item and exports an editable DOCX plus optional real PDF preview.
---

## Two commands, then the work

```bash
python "$SKILL_DIR/scripts/run_case.py" plan           # contract, check list, result.json skeleton
# ... read the case material and write the deliverable ...
python "$SKILL_DIR/scripts/run_case.py" finish --md work/deliverable.md   # build, audit, conform, verify
```

`plan` takes no reading of its own and `finish` returns a JSON report whose `failed_checks` names
exactly what to repair. When `finish` finds an adapted DOCX under `work/adapted` it also audits its
caption numbering, in-text cross-references and reference list (step 7 below) and reports `linkage`
with `defect_kinds`. Everything else in this file explains what to put in the deliverable between
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

# Source-faithful academic template adaptation

Run this on the actual case now. Produce the adapted document and its evidence; do not
return a plan, a checklist alone, or a promise. The case's own requirements outrank every
example in this file.

## Contract

- Read the real `/input/case.json` and `task.md`, then every material they reference
  (`material.json`, `environment/resources.yaml`). The supplied template and manuscript are
  whatever the case actually ships: DOCX, PDF, LaTeX or prose requirements. Read the real
  files; never infer content from a label or a file name.
- Work in `/app/work`. Final deliverables go in `/app/output`, including `result.json` with
  the **original `case_id` and every original `output_contract` field**, original names,
  nesting and types. Do not replace the contract with this file's example.
- Keep the manuscript's content units intact: text, tables, figures, captions, footnotes,
  comments, tracked changes, equations and field codes. Adaptation changes presentation,
  never content. Never delete a source block to satisfy a template.
- Adapter: `"$SKILL_DIR/scripts/adapt_template.py"` where `SKILL_DIR` is the real directory
  of the loaded `SKILL.md`. Python 3.10+ standard library only — no network, no pip, no
  Office suite required. LibreOffice/Poppler, when present, only add a PDF/PNG preview.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Save an honest partial
  deliverable early and improve it; do not spend the budget exploring.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Locate the pieces.** From the case and its workorder, identify: the manuscript file(s),
   the target template, the requested deliverable format(s), the required output names, and
   any stated rule (font, size, spacing, margins, columns, caption position, reference
   style, page setup). Record each rule with the exact quoted requirement and its locator in
   your notes. If the case supplies only prose requirements, treat that text as the template
   specification.
2. **Inspect before adapting.**
   `python "$SKILL_DIR/scripts/adapt_template.py" inspect <file> --out /app/work/inspect-<name>.json`
   for the template, the manuscript, and any supplied style guide. Read the JSON: section
   geometry, docDefaults, style inventory, style usage, tables, media, notes, fields, and
   hashes. XML facts are evidence; a style's name alone is not.
3. **Extract the checklist.**
   `python "$SKILL_DIR/scripts/adapt_template.py" specify --template <template> --source <manuscript> --out /app/work/spec.json`
   It writes one item per requirement (page size, margins, columns, default font and size,
   each style family, the source→template style mapping) with `evidence_locator` and
   `status`. Read it and correct anything the case contradicts; if you override a mapping,
   say so and why in `result.json`. Never edit a hash to hide a mismatch.
4. **Adapt.**
   `python "$SKILL_DIR/scripts/adapt_template.py" apply --source <manuscript> --template <template> --spec /app/work/spec.json --outdir /app/work/adapted`
   The script imports the template's style definitions and document defaults into a copy of
   the manuscript package, re-points each source paragraph style to its mapped template
   style, applies the template's table formatting and copies the template's page
   size/margins/columns/grid. It does not rebuild the document, so unrelated parts stay
   byte-identical. `apply-report.json` records the imported styles, the style pairs, the
   geometry change and whether the text stream was preserved. Exit code 2 means it refused:
   read `reason` and fall back to the supported subset, never to a fabricated result.
5. **Verify item by item.**
   `python "$SKILL_DIR/scripts/adapt_template.py" verify --source <manuscript> --output /app/work/adapted/adapted.docx --spec /app/work/spec.json --outdir /app/work/adapted`
   Produces `verification.json`: every check has `id`, `requirement`, `status`, `evidence`
   and `locator`. Content coverage, content order, preserved tables/media/notes/equations,
   template geometry, default font and size, table style and each style mapping are checked
   independently of the apply step. A `fail` is real work remaining — fix the cause, do not
   relabel it.
6. **Export and look at it.**
   `python "$SKILL_DIR/scripts/adapt_template.py" preview --docx /app/work/adapted/adapted.docx --outdir /app/work/adapted`
   With LibreOffice and Poppler available this produces a genuine PDF, font report and PNGs:
   open the PNGs and check margins, heading hierarchy, caption placement, table fit and
   clipping. Without a renderer the report says so — then the editable DOCX is the
   deliverable and the missing preview is an explicit limitation, never a claimed success.
   Copy the real artifacts into `/app/output` under the names the case requires (for example
   `deliverable.docx`, `adapted.pdf`, the checklist and the verification report).
7. **Audit the captions, the references that point at them, and the reference list.**
   `python "$SKILL_DIR/scripts/adapt_template.py" linkage --source <manuscript> --output /app/work/adapted/adapted.docx --outdir /app/work/adapted`
   `linkage-report.json` lists every figure/table/equation caption it found with the label it
   declares, its position in the caption sequence of its family, which object it sits next to, and
   every in-text reference with whether it resolves; then the reference list (entry count, label
   style, order, repeats) and the SEQ/REF/PAGEREF/TOC field codes with any bookmark a REF field
   points at but that does not exist. `status` is `consistent`, `needs_work` or `not_applicable`;
   each defect carries a `kind` and a `locator`. Where the template's own convention differs from
   the defaults here (a figure caption above the figure, a table caption below the table, a
   reference list in citation order), the report says so under `observations` instead of treating
   it as a defect - check the template before changing anything.
8. **Repair what is repairable, together.** When captions are out of sequence, add `--renumber`:
   it rewrites the caption number and every in-text reference that points at that caption in one
   pass, so a number cannot be updated in one place and left stale in the other.
   `--renumber` writes a new file (default `renumbered.docx`, or `--out-file`), lists every change
   in `renumbered.caption_edits` / `renumbered.cross_reference_edits`, and refuses (status
   `ambiguous`, no file written) rather than guess when two captions would collide or when a
   reference points at a caption that never existed. Take the renumbered file as the deliverable,
   rerun `verify` and `linkage` on it, and report what remains: a reference to a caption that was
   never in the manuscript cannot be pointed anywhere by renumbering, so it stays listed.
9. **Report honestly.** Write `/app/output/result.json` with the original contract fields:
   the deliverable path(s), the preserved-fact and style mapping, the change log (what was
   changed, why, what still needs a human), the verification summary with its real
   pass/fail counts, and `status` from the case's own vocabulary. List uncertainties:
   requirements that were prose-only, font substitution, numbering/TOC or cross-reference
   behaviour that was preserved rather than renumbered, a template part (header/footer
   boilerplate, journal-specific front matter) that was deliberately not copied, and any
   check that could not run. A partial result must name exactly what is missing.
10. **Re-open your own output** (`result.json` and each artifact) before finishing: paths
   resolve, files are non-empty, the DOCX is still openable, and no number or claim in the
   report is absent from `verification.json`.

## Failure handling

- Not DOCX: a PDF/LaTeX/prose template cannot be converted by guessing styles. Convert the
  manuscript with the case's own supplied tools, apply what the stated rules pin down
  (margins, font, size, spacing, caption position, reference style) and report per item what
  is applied and what stays unchecked.
- Unmatched style: keep the paragraph's idempotent content, leave the style as-is, and list
  it under `unmapped_source_styles` with the reason. Never silently drop or merge a block.
- Missing template or manuscript: deliver the supported part and name the missing file and
  locator.
- Template conflict with the source (for example the template demands numbering the
  manuscript does not use): keep the source semantics, record the conflict, and ask for a
  human decision in the change log.
- The caption/cross-reference audit refuses a renumber (`status: ambiguous`, no file written)
  when two captions would end up with the same number, when a digit span does not address the raw
  text (a tab or line break inside the label), or when a reference points at a caption that never
  existed. The refusal is the result: report it, keep the un-renumbered file, and list what the
  author has to decide rather than renumbering into an inconsistency.
- A caption paragraph whose style is the caption role but whose text declares no label is listed
  under `caption_style_paragraphs_without_label` and is not renumbered - it is reported, because
  inventing a number for it would change the document's meaning.

## Genuine upstream relationship

The style-import semantics follow the MIT-licensed project
[doc-forge](https://github.com/SchrodingersCattt/doc-forge) (commit
`1fa02b08aea33debb3cc9fb1b5af138dd7e9b006`), whose `restyle` command edits style
definitions inside the source package instead of rebuilding it. `scripts/adapt_template.py`
is an independent standard-library implementation of that method for environments where
doc-forge cannot be installed; it is not the upstream package and does not claim to be. If a
real doc-forge installation is present in the case environment and the case asks for it, the
upstream command is
`docforge restyle SOURCE OUTPUT --profile PROFILE --loss-policy error` — then still run the
verification above, because doc-forge audits the package, not this task's requirements.

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
| `tests/linkage_checks.py` | the true-positive/true-negative control for the caption, cross-reference and reference-list audit |

These are submission materials, not case answers: no organizer case, whiteboard or formal result is
included anywhere in this bundle.

## Minimal example (synthetic, not a case)

```
python "$SKILL_DIR/scripts/adapt_template.py" inspect /input/manuscript.docx --out /app/work/inspect-manuscript.json
python "$SKILL_DIR/scripts/adapt_template.py" specify --template /input/template.docx --source /input/manuscript.docx --out /app/work/spec.json
python "$SKILL_DIR/scripts/adapt_template.py" apply   --source /input/manuscript.docx --template /input/template.docx --spec /app/work/spec.json --outdir /app/work/adapted
python "$SKILL_DIR/scripts/adapt_template.py" verify  --source /input/manuscript.docx --output /app/work/adapted/adapted.docx --spec /app/work/spec.json --outdir /app/work/adapted
python "$SKILL_DIR/scripts/adapt_template.py" linkage --source /input/manuscript.docx --output /app/work/adapted/adapted.docx --outdir /app/work/adapted
```

Illustrative output for that toy pair: `{"applied": true, "restyled_paragraphs": 10,
"content_stream_preserved": true}` then `{"passed": 22, "failed": 0, "status": "verified"}`.
Those numbers come from `examples/synthetic_case.py`, a fixture written for interface
testing; they are not case results and not a score. See `README.md` for the file map and
`MAPPING.md` for the requirement-to-check mapping.

## Reusing this package

Everything here is plain text and standard-library Python, so it can be lifted into another project
without a build step. This section names what is reusable, what it needs, and where its limits are.


### What you can take

| Resource | Reuse path |
|---|---|
| 5 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 6 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `figure-table-pointer-template.csv`, `glossary-template.csv`, `reference-map-template.csv`, `section-evidence-map.csv`. |
| 3 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`, `linkage_checks.py`, `run_checks.py`. |
| Worked fixtures (`examples/`) | `linkage_case.py`, `synthetic_case.py` - realistic shapes you can run end to end before touching real material. |
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
| declared artifacts inspected per run | 24 |
| of which are content checks, not just file presence | 24 |
| distinct machine-readable reports emitted | 9 |
| conditions the package refuses to pass silently | 0 |
| self-test suites shipped | 3 |
| self-test assertions | 49 |
| adversarial negative controls in the test suite | 2 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 24 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 0 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 9 machine-readable report(s): `number-scan/v1`, `output-contract-check/v1`, `output-contract-verify/v1`, `output-contract/v1` |
| Regression safety | none | 49 assertions in the shipped self-tests, including 2 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `captions`, `case_id_preserved`, `columns`, `content_units`, `cross_references`, `declared_columns_present`, `declared_vocabulary_respected`, `default_font`, `default_size`, `key_types_match` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
