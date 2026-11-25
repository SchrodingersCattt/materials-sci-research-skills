---
name: template-aware-deck-editor
description: Use when supplied slides or a supplied PPTX template must be edited or extended — fill the template's own placeholders, inherit its master/layout/theme, keep every untouched part byte-identical, measure each text frame and deliver a real rendered preview.
---

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

# Template-aware deck editor

Run this on the actual case and deliver the deck. Do not rebuild a deck from scratch when a
template was supplied, and do not claim a template was used because the colours look similar.

## Contract

- Read the real `/input/case.json`, `task.md` and every material they reference — the template,
  the starting deck, the source paper, the slide workorder, `environment/resources.yaml`. Read
  the supplied PPTX to learn its layout names and placeholders; never assume a placeholder name.
- Work in `/app/work`; deliverables in `/app/output`, including `result.json` with the
  **original `case_id` and every original `output_contract` field**, original names, nesting and
  types.
- Tool: `"$SKILL_DIR/scripts/edit_slides.py"` (`SKILL_DIR` = the real directory of the loaded
  `SKILL.md`). Python 3.10+, standard library only: no network, no pip, no python-pptx. A
  LibreOffice renderer is optional and only adds the preview.
- Budget: 64 model requests, 900 s, 16384 output tokens per response. Deliver an honest deck
  early and improve it.
- The template's design is the author's decision, not yours: keep the master, layouts, theme
  fonts, theme colours and slide size exactly, and change only the content the case asks for.
- Contract conformance: after the deliverables and `result.json` exist, run
  `python "$SKILL_DIR/scripts/contract_check.py" verify --case /input/case.json --task /input/task.md --outdir /app/work/conformance`
  and repair every failed check before finishing; `conform --contract ... --output /app/output`
  reports the same checks per artifact.

## Do this

1. **Inspect the supplied deck.**
   `python "$SKILL_DIR/scripts/edit_slides.py" inspect <template-or-deck>.pptx --out /app/work/deck.json`
   Read the slide size in EMU and inches, the theme fonts and colour slots, the master, every
   layout with its placeholder types/indices, and every existing slide with its shapes, geometry
   and text. Write down which layout each new page should use and which placeholder each piece of
   content belongs in — by the layout's own name, not a guess.
2. **Plan the content.** One JSON file: `{"slides": [{"id": "...", "target_slide": 1, "title":
   {"text": "...", "source_locator": "p12"}, "body": {"lines": [...]}}, {"id": "...", "layout":
   "<layout name from step 1>", "title": {...}, "body": {...}}]}`. A `target_slide` (1-based visible presentation order, not slide XML filename) edits an
   existing page; giving `layout` instead clones that layout's page and appends it. Every text
   entry may carry the source locator it came from, so the deck can be traced back to the paper.
3. **Merge.**
   `... merge --deck <template>.pptx --plan /app/work/deck-plan.json --outdir /app/work/deck`
   The output keeps the master, layouts, theme and every untouched slide **byte-identical**;
   only the edited slides, the slide list, its relationships and the content-type table change.
   The merge report lists exactly which parts changed, which were added, and confirms the
   template parts did not.
4. **Check.**
   `... check --deck <template>.pptx --output /app/work/deck/edited.pptx --plan /app/work/deck-plan.json --outdir /app/work/deck`
   Verifies: the package opens with master + layout, the slide size and theme are unchanged, the
   master is the template's own, every template part is byte-identical, every slide resolves to a
   real layout, every declared line is present in the produced slides, and no placeholder is
   **estimated** to overflow its own box (the estimate's formula is in the report; treat it as a
   warning, not proof).
5. **Render and look.**
   `... preview --deck /app/work/deck/edited.pptx --outdir /app/work/deck/preview`
   With LibreOffice present this produces a real PDF and per-slide PNGs; open them and check the
   title/body hierarchy, that nothing runs off the slide, and that the theme's fonts and colours
   are actually in the render. Read the extracted PDF text too — the check that the declared
   lines survived the render. Without a renderer the report says so: the editable PPTX is then the
   deliverable and the missing preview is an explicit limitation.
6. **Write `result.json`** with the original contract fields: the editable source, the export,
   the content map (each slide's content with its source locator), the compliance checks with
   their real pass/fail counts, the exceptions (placeholders the layout lacks, overflow warnings,
   a missing renderer) and honest status.
7. **Re-open your own output** before finishing: the deck opens, the check report's status is
   what you claim, and no slide claims content that the source does not contain.

## Failure handling

- A placeholder the layout does not have: the merge reports it as `missing_placeholders`; put the
  content in the closest existing frame **and** record the substitution, rather than adding a new
  shape that breaks the template's layout inheritance.
- An unused supplied layout is instantiated from its text placeholders and linked to that actual layout; it does not clone an unrelated sample slide. A requested layout name that does not exist is reported as layout_not_found, never silently substituted.
- Text longer than its box: shorten it, split the page, or mark the overflow in the change log.
  Never shrink the font below the template's hierarchy to force a fit.
- A case that supplies the source as a PDF: extract its text with the tools actually present,
  keep the locators you can verify, and mark the rest as approximate.

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
python "$SKILL_DIR/scripts/edit_slides.py" inspect /input/template.pptx --out /app/work/deck.json
python "$SKILL_DIR/scripts/edit_slides.py" merge --deck /input/template.pptx --plan /app/work/deck-plan.json --outdir /app/work/deck
python "$SKILL_DIR/scripts/edit_slides.py" check --deck /input/template.pptx --output /app/work/deck/edited.pptx --plan /app/work/deck-plan.json --outdir /app/work/deck
python "$SKILL_DIR/scripts/edit_slides.py" preview --deck /app/work/deck/edited.pptx --outdir /app/work/deck/preview
```

Illustrative output for the fixture: 4 placeholders filled, 1 slide added, template parts
unchanged, 8/8 checks pass, and a rendered PDF whose text contains the filled lines. Those numbers
come from `examples/synthetic_case.py` — an interface fixture, not case results and not a score.
See `MAPPING.md`.

## v2 template regression checks
Run python tests/test_v2.py, and tests/run_checks.py --workdir /app/work/slide-tests-new.
Version 2 resolves target_slide through presentation.xml order, recognizes centered-title and subtitle placeholders, instantiates unused supplied layouts, and refuses unknown named layouts. Original master/layout/theme bytes remain untouched. New pages created from layouts copy text placeholders, not unrelated sample content or arbitrary graphics. Existing figures remain intact in copied slides; adding/replacing figures or real speaker notes is not implemented by this helper. Use installed presentation tools for those required operations and verify the resulting relationships. Never claim a figure or notes were added merely because text was written.
Package checks and overflow estimates are not rendering. Render and inspect real output when a renderer exists; if absent, state that visual verification was not performed. No score gain is claimed from synthetic regression tests.

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
# ... read examples/material/, write the deliverable and work/result.json ...
```

### Sample output (real transcript from these commands)

Paths in the transcript are written `<WORKDIR>` because they differ on every machine; everything else
is exactly what the commands printed.

| Command | Exit | Output |
|---|---|---|
| `contract_check.py extract` | 0 | `{"keys": 5, "files": 0, "columns": 0, "checklist": 7}` |
| `contract_check.py skeleton` | 0 | `{"keys": ["case_id", "confidence", "evidence_map", "key_findings", "limitations", "summary"]}` |

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
| 3 engine scripts (`scripts/`) | Run them directly - each is a standalone command with `--help`. They read only declared inputs and write their outputs where you point them, so they drop into another pipeline without a wrapper. |
| The declared-artifact model | Every output is derived from a specification file you can copy and edit, so adapting the package to a new case means editing data, not code. |
| 7 templates (`templates/`) | Copy and fill: `change-log-template.csv`, `deliverable-plan-template.json`, `figure-table-pointer-template.csv`, `glossary-template.csv`, `page-deviation-record.csv`, `page-golden-standard.csv` and more. |
| 4 self-test suites (`tests/`) | Run them to reproduce every claim made in this package: `gain_checks.py`, `run_checks.py`, `test_v2.py`, `validate_package.py`. |
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
| declared artifacts inspected per run | 21 |
| of which are content checks, not just file presence | 21 |
| distinct machine-readable reports emitted | 7 |
| conditions the package refuses to pass silently | 2 |
| self-test suites shipped | 4 |
| self-test assertions | 20 |
| adversarial negative controls in the test suite | 2 |

### The before/after, under identical input

Both conditions receive the same material and the same tool permissions; the only difference is
whether this skill is loaded.

| Step | Baseline agent | With this package |
|---|---|---|
| Artifact inspection | eyeballed, or skipped under time pressure | 21 named checks run on the real bytes, each with a locator and a pass/fail verdict |
| Failure discovery | found when a reviewer notices, after delivery | 2 conditions stop the run and are reported instead of passing silently |
| Re-checking after an edit | repeat the work by hand | re-run the engine; the checks are deterministic and standard-library only |
| Evidence of what was checked | a sentence saying it was checked | 7 machine-readable report(s): `deck-check/v1`, `deck-inspection/v1`, `deck-merge/v1`, `deck-preview/v1` |
| Regression safety | none | 20 assertions in the shipped self-tests, including 2 negative controls that must fail |

The checks are the concrete form of "less manual work": each one is a judgement a person would
otherwise have to make by hand, on every run, and would have to remember to make at all. Named checks
include `case_id_preserved`, `declared_columns_present`, `declared_content_present`, `declared_vocabulary_respected`, `intended_slide_content`, `key_types_match`, `master_kept`, `no_estimated_overflow`, `no_placeholders`, `openable` and more.

### Honest scope of the claim

The counts are structural: they say how much verification is automated, not how much wall-clock time a
particular person saves. The package does not measure the baseline agent's behaviour, because it cannot
observe a run it is not part of - so the comparison above is between *what is automated* and *what
otherwise falls to manual review*, which the package can state as fact.
